import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ProjectStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    QUEUED = "QUEUED", "Queued"
    TRANSCRIBING = "TRANSCRIBING", "Transcribing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


_NON_TERMINAL = (
    ProjectStatus.PENDING,
    ProjectStatus.QUEUED,
    ProjectStatus.TRANSCRIBING,
)


def mark_stale_as_failed(projects):
    """Flip any non-terminal project whose updated_at is older than the
    configured stale timeout to FAILED. Mutates and saves the rows in place."""
    timeout = getattr(settings, "TRANSCRIBE_STALE_TIMEOUT_SECONDS", 1800)
    if timeout <= 0:
        return projects
    cutoff = timezone.now() - timedelta(seconds=timeout)
    error_msg = f"Marked stale: no progress for {timeout} seconds"
    for p in projects:
        if p.status not in _NON_TERMINAL:
            continue
        if p.updated_at is None or p.updated_at >= cutoff:
            continue
        p.status = ProjectStatus.FAILED
        p.error = error_msg
        p.save(update_fields=["status", "error", "updated_at"])
    return projects


def _new_id() -> str:
    return str(uuid.uuid4())


class Project(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=_new_id, editable=False)
    user_sub = models.CharField(max_length=128, db_index=True)
    original_filename = models.CharField(max_length=512)
    language = models.CharField(max_length=16, null=True, blank=True)
    status = models.CharField(
        max_length=32, choices=ProjectStatus.choices, default=ProjectStatus.PENDING
    )
    progress = models.IntegerField(default=0)
    error = models.TextField(null=True, blank=True)
    source_key = models.CharField(max_length=1024)
    srt_key = models.CharField(max_length=1024, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "language": self.language,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "has_srt": bool(self.srt_key),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
