FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# curl: used here to fetch the Whisper model directly from the HuggingFace
#       CDN (bypasses huggingface_hub's Xet + retry layers, which were
#       causing minute-long stalls on small JSON files).
# ffmpeg: used by faster-whisper at runtime to decode media to PCM.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first so they cache across code changes.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Whisper model: DIRECT curl download into the image
# ---------------------------------------------------------------------------
# faster-whisper accepts either a model-size string (which triggers an HF
# download at first use) OR a local directory path (which it just loads).
# We do the download here as straight HTTP GETs against the HF CDN, then
# point the app at the local path via WHISPER_MODEL_PATH. Result: zero HF
# calls at container start, no Xet, no tokenizer.json retry stalls.
# ---------------------------------------------------------------------------
ARG WHISPER_MODEL=tiny
ARG WHISPER_DEVICE=cpu
ARG WHISPER_COMPUTE_TYPE=int8
ARG HF_TOKEN=""
ENV WHISPER_MODEL=${WHISPER_MODEL} \
    WHISPER_DEVICE=${WHISPER_DEVICE} \
    WHISPER_COMPUTE_TYPE=${WHISPER_COMPUTE_TYPE} \
    HF_TOKEN=${HF_TOKEN} \
    HUGGING_FACE_HUB_TOKEN=${HF_TOKEN} \
    HF_XET_HIGH_PERFORMANCE=1 \
    HF_HUB_DISABLE_PROGRESS_BARS=1 \
    HF_HUB_DOWNLOAD_TIMEOUT=120 \
    HF_HUB_ETAG_TIMEOUT=60 \
    WHISPER_MODEL_PATH=/opt/whisper-models/faster-whisper-${WHISPER_MODEL}

RUN set -eu; \
    REPO="https://huggingface.co/Systran/faster-whisper-${WHISPER_MODEL}/resolve/main"; \
    OUT="${WHISPER_MODEL_PATH}"; \
    mkdir -p "${OUT}"; \
    echo "===== Whisper DIRECT curl download ====="; \
    echo "model       = ${WHISPER_MODEL}"; \
    echo "compute_type= ${WHISPER_COMPUTE_TYPE}"; \
    echo "source      = ${REPO}"; \
    echo "destination = ${OUT}"; \
    fetch() { \
        url="$1"; dest="$2"; required="$3"; \
        echo "----- GET ${url}"; \
        start=$(date +%s); \
        if curl --fail --location --silent --show-error \
                --retry 5 --retry-delay 2 --retry-max-time 600 \
                --connect-timeout 30 --max-time 900 \
                --write-out "  http_code=%{http_code} bytes=%{size_download} time=%{time_total}s avg=%{speed_download}B/s\n" \
                --output "${dest}" \
                "${url}"; then \
            ls -lh "${dest}"; \
            echo "  ✓ saved in $(( $(date +%s) - start ))s"; \
        else \
            rc=$?; \
            if [ "${required}" = "yes" ]; then \
                echo "  ✗ REQUIRED file failed (curl rc=${rc}) — aborting build"; \
                return 1; \
            else \
                echo "  ⚠ optional file missing (curl rc=${rc}) — continuing"; \
                rm -f "${dest}"; \
            fi; \
        fi; \
    }; \
    fetch "${REPO}/config.json"               "${OUT}/config.json"               yes; \
    fetch "${REPO}/tokenizer.json"            "${OUT}/tokenizer.json"            yes; \
    fetch "${REPO}/preprocessor_config.json"  "${OUT}/preprocessor_config.json"  no;  \
    fetch "${REPO}/vocabulary.txt"            "${OUT}/vocabulary.txt"            no;  \
    fetch "${REPO}/model.bin"                 "${OUT}/model.bin"                 yes; \
    echo "===== Whisper DIRECT curl download DONE ====="; \
    ls -lh "${OUT}"; \
    du -sh "${OUT}"

# Verify the curl'd bytes are actually a valid CTranslate2 model by loading
# them through faster-whisper. Catches a truncated model.bin at build time
# instead of crashing the first task in production.
COPY app/whisper_loader.py /opt/whisper_loader.py
RUN echo "===== Verifying model files load cleanly =====" \
    && python /opt/whisper_loader.py --verify-only \
    && echo "===== Model verified ====="

# Don't leak the token into runtime image layers.
ENV HF_TOKEN="" HUGGING_FACE_HUB_TOKEN=""

# Copy the app.
COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
