from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ProjectStatus:
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    TRANSCRIBING = "TRANSCRIBING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_sub: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=ProjectStatus.PENDING, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    srt_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "language": self.language,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "has_srt": self.srt_key is not None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
