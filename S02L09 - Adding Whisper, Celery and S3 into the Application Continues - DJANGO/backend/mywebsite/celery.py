import logging
import os

from celery import Celery
from celery.signals import worker_process_init

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mywebsite.settings")

logger = logging.getLogger(__name__)

app = Celery("subly")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
# Tasks live in the `myapp/celery/` subpackage, not the conventional
# `myapp/tasks.py`, so default autodiscovery misses them. Point it there too.
app.autodiscover_tasks(["myapp.celery"])

# Hard upper bound so a hung task (network stall, corrupt audio) eventually
# frees the worker slot instead of sitting in STARTED forever.
app.conf.update(
    task_soft_time_limit=60 * 60,        # 1 hour - raises SoftTimeLimitExceeded
    task_time_limit=60 * 60 + 60,        # +1 minute grace, then SIGKILL
)


@worker_process_init.connect
def _prewarm_whisper(**_kwargs) -> None:
    """Load the Whisper model once when the worker process boots so the
    first task doesn't pay the model load cost while the user watches Flower."""
    import django

    django.setup()
    from django.conf import settings

    logger.info(
        "worker_process_init: pre-warming Whisper model=%s device=%s compute_type=%s",
        settings.WHISPER["MODEL"],
        settings.WHISPER["DEVICE"],
        settings.WHISPER["COMPUTE_TYPE"],
    )
    try:
        from myapp.celery.tasks import _get_model

        _get_model()
        logger.info("worker_process_init: Whisper model loaded and cached in worker process")
    except Exception:
        logger.exception("worker_process_init: failed to pre-warm Whisper model")
