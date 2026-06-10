"""Whisper model loader with explicit, real-time download progress logging.

`huggingface_hub` (and its newer Xet downloader) does not emit byte-level
progress to stdout/stderr at INFO level, which makes a slow first-time
download look identical to a hang. This module wraps the load in a small
background thread that polls the HF cache directory every couple of seconds
and logs its growth — independent of which downloader is doing the work.

In production we don't hit that path at all: the Docker build curl's the
model files into /opt/whisper-models/faster-whisper-<size>/ ahead of time,
and this loader detects that directory via WHISPER_MODEL_PATH and skips
HuggingFace entirely. The CacheWatcher exists for the dev / outside-Docker
fallback case.

Importable from the running app *and* runnable as a script at Docker build
time (see backend/Dockerfile) so the build log shows the same progress
output as the runtime log.
"""
from __future__ import annotations

import argparse
import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(os.environ.get("HF_HOME", "/root/.cache/huggingface"))


LogFn = Callable[[str], None]


def _default_log(msg: str) -> None:
    if logger.handlers or logging.getLogger().handlers:
        logger.info(msg)
    else:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _dir_size_bytes(path: Path) -> int:
    try:
        total = 0
        for p in path.rglob("*"):
            try:
                if p.is_file():
                    total += p.stat().st_size
            except OSError:
                continue
        return total
    except FileNotFoundError:
        return 0


def _fmt_mb(b: int) -> str:
    return f"{b / (1024 * 1024):.1f} MB"


class CacheWatcher:
    """Context manager: polls the HF cache dir and logs growth + rate."""

    def __init__(
        self,
        cache_dir: Path,
        label: str,
        interval: float = 2.0,
        log: LogFn = _default_log,
        min_delta_mb: float = 5.0,
        heartbeat_seconds: float = 10.0,
    ) -> None:
        self.cache_dir = cache_dir
        self.label = label
        self.interval = interval
        self.log = log
        self.min_delta_mb = min_delta_mb
        self.heartbeat_seconds = heartbeat_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.start_size = 0
        self.t0 = 0.0

    def __enter__(self) -> "CacheWatcher":
        self.start_size = _dir_size_bytes(self.cache_dir)
        self.t0 = time.monotonic()
        self.log(
            f"[{self.label}] cache watcher START: dir={self.cache_dir} "
            f"initial={_fmt_mb(self.start_size)}"
        )
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        end_size = _dir_size_bytes(self.cache_dir)
        delta = max(end_size - self.start_size, 0)
        elapsed = time.monotonic() - self.t0
        avg = (delta / elapsed) / (1024 * 1024) if elapsed > 0 else 0
        self.log(
            f"[{self.label}] cache watcher STOP: final={_fmt_mb(end_size)} "
            f"downloaded={_fmt_mb(delta)} elapsed={elapsed:.1f}s "
            f"avg_rate={avg:.2f} MB/s"
        )

    def _run(self) -> None:
        last_logged_mb = 0.0
        last_log_t = self.t0
        first_emit = True
        stall_warned_for_mb = -1.0
        while not self._stop.is_set():
            size = _dir_size_bytes(self.cache_dir)
            downloaded_mb = max((size - self.start_size) / (1024 * 1024), 0.0)
            since_last_mb = downloaded_mb - last_logged_mb
            elapsed = time.monotonic() - self.t0
            now = time.monotonic()
            time_since_log = now - last_log_t
            avg_rate = downloaded_mb / elapsed if elapsed > 0 else 0.0

            big_change = since_last_mb >= self.min_delta_mb
            heartbeat = time_since_log >= self.heartbeat_seconds

            if first_emit and downloaded_mb > 0:
                self.log(
                    f"[{self.label}] 📥 first bytes: {downloaded_mb:.1f} MB after "
                    f"{elapsed:.1f}s"
                )
                last_logged_mb = downloaded_mb
                last_log_t = now
                first_emit = False
            elif big_change:
                inst_rate = since_last_mb / time_since_log if time_since_log > 0 else 0
                self.log(
                    f"[{self.label}] 📥 +{since_last_mb:.1f} MB this chunk → "
                    f"total {downloaded_mb:.1f} MB (cache={_fmt_mb(size)}) "
                    f"elapsed={elapsed:.1f}s inst_rate={inst_rate:.2f} MB/s "
                    f"avg_rate={avg_rate:.2f} MB/s"
                )
                last_logged_mb = downloaded_mb
                last_log_t = now
                stall_warned_for_mb = -1.0
            elif heartbeat:
                if since_last_mb < 0.5:
                    if stall_warned_for_mb != downloaded_mb:
                        self.log(
                            f"[{self.label}] ⏳ STALLED — no growth for "
                            f"{int(time_since_log)}s, holding at "
                            f"{downloaded_mb:.1f} MB "
                            f"(elapsed={elapsed:.1f}s) — HF likely retrying a "
                            f"small-file timeout, this is usually OK"
                        )
                        stall_warned_for_mb = downloaded_mb
                else:
                    inst_rate = since_last_mb / time_since_log if time_since_log > 0 else 0
                    self.log(
                        f"[{self.label}] 🐢 slow trickle: +{since_last_mb:.2f} MB "
                        f"in last {int(time_since_log)}s → total {downloaded_mb:.1f} MB "
                        f"(inst_rate={inst_rate:.3f} MB/s)"
                    )
                    last_logged_mb = downloaded_mb
                    stall_warned_for_mb = -1.0
                last_log_t = now

            self._stop.wait(self.interval)


def _local_model_path() -> Path | None:
    """Return the local model directory if WHISPER_MODEL_PATH is set and
    contains a `model.bin` (i.e. the build's curl step has populated it)."""
    raw = os.environ.get("WHISPER_MODEL_PATH")
    if not raw:
        return None
    p = Path(raw)
    if p.is_dir() and (p / "model.bin").is_file():
        return p
    return None


def download_and_load(
    model: str,
    device: str,
    compute_type: str,
    log: LogFn = _default_log,
):
    """Load and return a `faster_whisper.WhisperModel`.

    Prefers a locally-baked model directory (WHISPER_MODEL_PATH) — set by the
    Dockerfile's curl step. Falls back to HuggingFace Hub if the directory is
    missing (e.g. running outside Docker).
    """
    log(
        f"whisper_loader: requested model={model} device={device} "
        f"compute_type={compute_type}"
    )

    from faster_whisper import WhisperModel  # local import keeps build step light

    local = _local_model_path()
    if local is not None:
        bin_size = (local / "model.bin").stat().st_size
        files = sorted(p.name for p in local.iterdir() if p.is_file())
        log(
            f"whisper_loader: LOCAL path={local} model.bin={_fmt_mb(bin_size)} "
            f"files={files}"
        )
        t0 = time.monotonic()
        m = WhisperModel(str(local), device=device, compute_type=compute_type)
        log(
            f"whisper_loader: model READY (local) elapsed={time.monotonic() - t0:.2f}s"
        )
        return m

    log(
        "whisper_loader: no local model path "
        f"(WHISPER_MODEL_PATH={os.environ.get('WHISPER_MODEL_PATH', '<unset>')}) "
        "— falling back to HuggingFace Hub"
    )
    log(
        "whisper_loader: env "
        f"HF_HOME={os.environ.get('HF_HOME', '<default>')} "
        f"HF_XET_HIGH_PERFORMANCE={os.environ.get('HF_XET_HIGH_PERFORMANCE', '<unset>')} "
        f"HF_TOKEN={'set' if os.environ.get('HF_TOKEN') else 'unset'}"
    )
    pre_size = _dir_size_bytes(_CACHE_DIR)
    log(f"whisper_loader: HF cache pre-load size={_fmt_mb(pre_size)}")

    t0 = time.monotonic()
    with CacheWatcher(_CACHE_DIR, label=f"whisper:{model}", log=log):
        m = WhisperModel(model, device=device, compute_type=compute_type)
    log(
        f"whisper_loader: model READY (HF) model={model} "
        f"total_elapsed={time.monotonic() - t0:.2f}s"
    )
    return m


def _main_cli() -> None:
    p = argparse.ArgumentParser(
        description="Load a faster-whisper model (local path preferred)."
    )
    p.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "tiny"))
    p.add_argument("--device", default=os.environ.get("WHISPER_DEVICE", "cpu"))
    p.add_argument(
        "--compute-type", default=os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
    )
    p.add_argument(
        "--verify-only",
        action="store_true",
        help="Load and immediately discard the model — used by the Docker "
             "build to verify the curl'd files are valid before image ships.",
    )
    args = p.parse_args()

    m = download_and_load(args.model, args.device, args.compute_type)
    if args.verify_only:
        del m
        _default_log("whisper_loader: --verify-only set; model dropped from RAM")


if __name__ == "__main__":
    _main_cli()
