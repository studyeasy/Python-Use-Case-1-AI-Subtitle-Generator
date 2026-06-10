import logging

from celery import Celery
from celery.signals import worker_process_init

from app.config import settings
from app.db.session import Base, engine
from app.models import project as _project_model  # noqa: F401  (register ORM model)

logger = logging.getLogger(__name__)

celery_app = Celery(
    "subly",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.transcribe"],
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    # Hard upper bound so a hung task (network stall, corrupt audio) eventually
    # frees the worker slot instead of sitting in STARTED forever.
    task_soft_time_limit=60 * 60,        # 1 hour - raises SoftTimeLimitExceeded
    task_time_limit=60 * 60 + 60,        # +1 minute grace, then SIGKILL
)

# Make sure the projects table exists when the worker boots. Safe to call
# on every start; SQLAlchemy is a no-op when tables already exist.
Base.metadata.create_all(bind=engine)


@worker_process_init.connect
def _prewarm_whisper(**_kwargs) -> None:
    """Load the Whisper model once when the worker process boots so the
    first task doesn't pay the multi-hundred-MB download + load cost while
    the user watches Flower."""
    logger.info(
        "worker_process_init: pre-warming Whisper model=%s device=%s compute_type=%s",
        settings.whisper_model,
        settings.whisper_device,
        settings.whisper_compute_type,
    )
    try:
        from app.tasks.transcribe import _get_model

        _get_model()
        logger.info("worker_process_init: Whisper model loaded and cached in worker process")
    except Exception:
        logger.exception("worker_process_init: failed to pre-warm Whisper model")
