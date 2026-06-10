import logging
import os
import tempfile
import time
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from myapp.models.project import Project, ProjectStatus
from myapp.services.s3_service import S3Service

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from myapp.celery.whisper_service import download_and_load

        _model = download_and_load(
            settings.WHISPER["MODEL"],
            settings.WHISPER["DEVICE"],
            settings.WHISPER["COMPUTE_TYPE"],
            log=logger.info,
        )
    else:
        logger.info("Whisper model already loaded in this worker process — reusing")
    return _model


def _format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


@shared_task(name="transcribe", bind=True)
def transcribe(self, project_id: str) -> dict:
    task_t0 = time.monotonic()
    logger.info("=" * 70)
    logger.info("transcribe TASK START: project_id=%s task_id=%s", project_id, self.request.id)
    logger.info("=" * 70)

    s3 = S3Service()
    logger.info("[1/9] S3 service initialised for project=%s", project_id)

    work_dir: Path | None = None
    try:
        logger.info("[2/9] Looking up project row: project=%s", project_id)
        project = Project.objects.filter(pk=project_id).first()
        if project is None:
            logger.error("[2/9] Project %s NOT FOUND in DB — aborting task", project_id)
            return {"ok": False, "error": "project not found"}
        logger.info(
            "[2/9] Project found: id=%s status=%s source_key=%s language=%s filename=%s",
            project.id,
            project.status,
            project.source_key,
            project.language,
            project.original_filename,
        )

        logger.info("[3/9] Flipping status → TRANSCRIBING, progress → 0")
        project.status = ProjectStatus.TRANSCRIBING
        project.progress = 0
        project.save(update_fields=["status", "progress", "updated_at"])

        work_dir = Path(tempfile.mkdtemp(prefix=f"subly-{project_id}-"))
        src_name = Path(project.original_filename).name or "source"
        src_path = work_dir / src_name
        logger.info("[4/9] Temp workdir created: %s (source file → %s)", work_dir, src_path)

        meta = s3.head_object(project.source_key)
        if meta is None:
            raise RuntimeError(
                f"S3 head_object failed for key={project.source_key} — "
                "object missing or worker lacks s3:GetObject permission"
            )
        size_bytes = int(meta.get("ContentLength") or 0)
        size_mb = size_bytes / (1024 * 1024)
        logger.info(
            "[5/9] S3 download starting: key=%s size=%.2f MB",
            project.source_key, size_mb,
        )

        state = {"bytes": 0, "last_log_mb": 0, "t0": time.monotonic()}

        def _on_chunk(n: int) -> None:
            state["bytes"] += n
            mb = state["bytes"] // (1024 * 1024)
            if mb - state["last_log_mb"] >= 25 or (size_bytes and state["bytes"] >= size_bytes):
                state["last_log_mb"] = mb
                elapsed = time.monotonic() - state["t0"]
                rate = (state["bytes"] / 1024 / 1024) / elapsed if elapsed > 0 else 0
                pct = (state["bytes"] / size_bytes * 100) if size_bytes else 0
                logger.info(
                    "      …S3 download progress: %d MB / %.0f MB (%.1f%%) @ %.2f MB/s",
                    mb, size_mb, pct, rate,
                )

        s3.download_to_path(project.source_key, str(src_path), callback=_on_chunk)
        on_disk = os.path.getsize(src_path)
        logger.info(
            "[5/9] S3 download complete: on-disk=%d bytes (expected=%d)",
            on_disk, size_bytes,
        )

        logger.info("[6/9] Loading Whisper model (no-op if pre-warmed)")
        model = _get_model()

        logger.info(
            "[7/9] Whisper transcribe START: file=%s language=%s vad_filter=True",
            src_path, project.language or "auto",
        )
        whisper_t0 = time.monotonic()
        segments, info = model.transcribe(
            str(src_path),
            language=project.language or None,
            vad_filter=True,
        )
        duration = float(getattr(info, "duration", 0) or 0)
        detected_lang = getattr(info, "language", None)
        lang_prob = getattr(info, "language_probability", None)
        logger.info(
            "[7/9] Whisper transcribe initialised: audio_duration=%.2fs "
            "detected_language=%s language_probability=%s",
            duration, detected_lang, lang_prob,
        )

        srt_path = work_dir / (Path(src_name).stem + ".srt")
        last_pct = -1
        segment_count = 0
        with srt_path.open("w", encoding="utf-8") as fh:
            for idx, segment in enumerate(segments, start=1):
                start_ts = _format_timestamp(segment.start)
                end_ts = _format_timestamp(segment.end)
                text = (segment.text or "").strip()
                fh.write(f"{idx}\n{start_ts} --> {end_ts}\n{text}\n\n")
                segment_count = idx

                if idx == 1:
                    logger.info(
                        "[7/9] First segment yielded after %.2fs (cold-start latency)",
                        time.monotonic() - whisper_t0,
                    )
                if idx % 25 == 0:
                    logger.info(
                        "[7/9] …%d segments written, audio cursor=%.2fs / %.2fs",
                        idx, segment.end, duration,
                    )

                if duration > 0:
                    pct = int(min(99, (segment.end / duration) * 100))
                    if pct - last_pct >= 5:
                        last_pct = pct
                        # Bump updated_at explicitly: QuerySet.update() bypasses
                        # auto_now, and stale-detection relies on this timestamp
                        # moving while transcription is progressing.
                        Project.objects.filter(pk=project_id).update(
                            progress=pct, updated_at=timezone.now()
                        )
                        logger.info("[7/9] progress → %d%% (DB updated)", pct)

        logger.info(
            "[7/9] Whisper transcribe DONE: segments=%d srt=%s elapsed=%.2fs",
            segment_count, srt_path, time.monotonic() - whisper_t0,
        )

        srt_key = f"{settings.S3['SUBTITLE_PREFIX']}{project_id}/{srt_path.name}"
        logger.info("[8/9] Uploading SRT → s3://%s/%s", s3.bucket, srt_key)
        with srt_path.open("rb") as fh:
            s3.upload_fileobj(srt_key, fh, content_type="application/x-subrip")

        Project.objects.filter(pk=project_id).update(
            srt_key=srt_key,
            progress=100,
            status=ProjectStatus.COMPLETED,
            updated_at=timezone.now(),
        )
        logger.info(
            "[9/9] transcribe TASK COMPLETED: project=%s srt_key=%s total_elapsed=%.2fs",
            project_id, srt_key, time.monotonic() - task_t0,
        )
        return {"ok": True, "srt_key": srt_key}

    except Exception as exc:
        logger.exception(
            "transcribe TASK FAILED: project=%s elapsed=%.2fs error=%s",
            project_id, time.monotonic() - task_t0, exc,
        )
        try:
            Project.objects.filter(pk=project_id).update(
                status=ProjectStatus.FAILED,
                error=str(exc)[:2000],
                updated_at=timezone.now(),
            )
            logger.info("Project %s marked FAILED in DB", project_id)
        except Exception:
            logger.exception("Failed to mark project %s as FAILED", project_id)
        raise
    finally:
        if work_dir is not None:
            logger.info("Cleaning up temp workdir: %s", work_dir)
            for p in sorted(work_dir.rglob("*"), reverse=True):
                try:
                    p.unlink() if p.is_file() else p.rmdir()
                except OSError as exc:
                    logger.warning("Cleanup failed for %s: %s", p, exc)
            try:
                work_dir.rmdir()
            except OSError as exc:
                logger.warning("Cleanup failed for workdir %s: %s", work_dir, exc)
        logger.info(
            "transcribe TASK END: project=%s total_elapsed=%.2fs",
            project_id, time.monotonic() - task_t0,
        )
