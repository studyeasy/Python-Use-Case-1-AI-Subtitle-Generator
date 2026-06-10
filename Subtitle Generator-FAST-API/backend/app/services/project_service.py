import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project, ProjectStatus

_NON_TERMINAL = (
    ProjectStatus.PENDING,
    ProjectStatus.QUEUED,
    ProjectStatus.TRANSCRIBING,
)


def new_project_id() -> str:
    return str(uuid.uuid4())


def create_project(
    db: Session,
    *,
    project_id: str,
    user_sub: str,
    original_filename: str,
    language: str | None,
    source_key: str,
) -> Project:
    project = Project(
        id=project_id,
        user_sub=user_sub,
        original_filename=original_filename,
        language=language,
        status=ProjectStatus.PENDING,
        progress=0,
        source_key=source_key,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_for_user(db: Session, *, project_id: str, user_sub: str) -> Project | None:
    stmt = select(Project).where(Project.id == project_id, Project.user_sub == user_sub)
    return db.execute(stmt).scalar_one_or_none()


def get_by_id(db: Session, *, project_id: str) -> Project | None:
    return db.get(Project, project_id)


def list_for_user(db: Session, *, user_sub: str) -> list[Project]:
    stmt = (
        select(Project)
        .where(Project.user_sub == user_sub)
        .order_by(Project.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def update_status(
    db: Session, *, project: Project, status: str, error: str | None = None
) -> Project:
    project.status = status
    if error is not None:
        project.error = error
    db.commit()
    db.refresh(project)
    return project


def update_progress(db: Session, *, project: Project, progress: int) -> Project:
    project.progress = max(0, min(100, progress))
    db.commit()
    db.refresh(project)
    return project


def set_srt_key(db: Session, *, project: Project, srt_key: str) -> Project:
    project.srt_key = srt_key
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, *, project: Project) -> None:
    db.delete(project)
    db.commit()


def mark_stale_as_failed(db: Session, projects: list[Project]) -> list[Project]:
    """Flip non-terminal projects that haven't been updated within the
    stale-timeout window to FAILED. Returns the (possibly mutated) list."""
    timeout = settings.transcribe_stale_timeout_seconds
    if timeout <= 0 or not projects:
        return projects
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout)
    changed = False
    for p in projects:
        if p.status not in _NON_TERMINAL:
            continue
        updated = p.updated_at
        if updated is None:
            continue
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if updated < cutoff:
            p.status = ProjectStatus.FAILED
            p.error = f"Marked stale: no progress for {timeout} seconds"
            changed = True
    if changed:
        db.commit()
        for p in projects:
            db.refresh(p)
    return projects
