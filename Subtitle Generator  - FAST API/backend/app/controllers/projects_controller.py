from pathlib import PurePosixPath
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.cognito import get_current_user
from app.celery_app import celery_app
from app.config import settings
from app.db.session import get_db
from app.models.project import ProjectStatus
from app.schemas.project_schema import (
    PresignedUrlResponse,
    ProjectCreateResponse,
    ProjectSummary,
)
from app.services import project_service
from app.services.s3_service import S3Service, get_s3_service

router = APIRouter(prefix="/projects", tags=["Projects"])


def _sanitize_filename(name: str) -> str:
    base = PurePosixPath(name.replace("\\", "/")).name
    return base or "upload.bin"


@router.post(
    "",
    response_model=ProjectCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a media file and queue transcription",
)
def create_project(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    db: Session = Depends(get_db),
    claims: dict[str, Any] = Depends(get_current_user),
    s3: S3Service = Depends(get_s3_service),
) -> ProjectCreateResponse:
    user_sub = claims.get("sub")
    if not user_sub:
        raise HTTPException(status_code=401, detail="Invalid user claims")

    if not settings.s3_bucket:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")

    filename = _sanitize_filename(file.filename or "upload.bin")
    lang = (language or "").strip().lower() or None

    project_id = project_service.new_project_id()
    source_key = f"{settings.s3_upload_prefix}{project_id}/{filename}"

    try:
        s3.upload_fileobj(source_key, file.file, content_type=file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"S3 upload failed: {exc}") from exc

    project = project_service.create_project(
        db,
        project_id=project_id,
        user_sub=user_sub,
        original_filename=filename,
        language=lang,
        source_key=source_key,
    )
    project_service.update_status(db, project=project, status=ProjectStatus.QUEUED)

    # Use project_id as the Celery task_id so we can revoke a running task
    # later without persisting a separate column.
    celery_app.send_task("transcribe", args=[project_id], task_id=project_id)

    return ProjectCreateResponse(id=project.id, status=project.status)


@router.get("", response_model=list[ProjectSummary], summary="List the user's projects")
def list_projects(
    db: Session = Depends(get_db),
    claims: dict[str, Any] = Depends(get_current_user),
) -> list[ProjectSummary]:
    user_sub = claims.get("sub") or ""
    projects = project_service.list_for_user(db, user_sub=user_sub)
    project_service.mark_stale_as_failed(db, projects)
    return [ProjectSummary(**p.to_dict()) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectSummary,
    summary="Get a single project (status + progress)",
)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    claims: dict[str, Any] = Depends(get_current_user),
) -> ProjectSummary:
    user_sub = claims.get("sub") or ""
    project = project_service.get_for_user(db, project_id=project_id, user_sub=user_sub)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project_service.mark_stale_as_failed(db, [project])
    return ProjectSummary(**project.to_dict())


@router.get(
    "/{project_id}/srt",
    response_model=PresignedUrlResponse,
    summary="Get a time-limited download URL for the SRT",
)
def get_project_srt(
    project_id: str,
    db: Session = Depends(get_db),
    claims: dict[str, Any] = Depends(get_current_user),
    s3: S3Service = Depends(get_s3_service),
) -> PresignedUrlResponse:
    user_sub = claims.get("sub") or ""
    project = project_service.get_for_user(db, project_id=project_id, user_sub=user_sub)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.srt_key:
        raise HTTPException(status_code=409, detail="SRT is not ready yet")
    url = s3.presign_get(project.srt_key)
    return PresignedUrlResponse(url=url)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project and its S3 artifacts",
)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    claims: dict[str, Any] = Depends(get_current_user),
    s3: S3Service = Depends(get_s3_service),
) -> None:
    user_sub = claims.get("sub") or ""
    project = project_service.get_for_user(db, project_id=project_id, user_sub=user_sub)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    # SIGKILL because a stuck task is often blocked inside a C-level socket
    # read (e.g. boto3 download) which won't respond to SIGTERM. Revoke is a
    # no-op for tasks that already finished.
    try:
        celery_app.control.revoke(project_id, terminate=True, signal="SIGKILL")
    except Exception:
        pass
    if project.source_key:
        s3.delete(project.source_key)
    if project.srt_key:
        s3.delete(project.srt_key)
    project_service.delete_project(db, project=project)
