from pathlib import PurePosixPath

from flask import g, request
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.auth import require_auth
from app.celery_app import celery_app
from app.config import settings
from app.db.session import SessionLocal
from app.models.project import ProjectStatus
from app.schemas.project_schema import (
    PresignedUrlResponse,
    ProjectCreateResponse,
    ProjectSummary,
)
from app.services import project_service
from app.services.s3_service import S3Service

blp = Blueprint(
    "Projects", __name__, description="Subtitle projects (upload, status, SRT download)"
)


def _sanitize_filename(name: str) -> str:
    base = PurePosixPath((name or "").replace("\\", "/")).name
    return base or "upload.bin"


@blp.route("")
class ProjectsCollection(MethodView):
    @require_auth
    @blp.response(200, ProjectSummary(many=True))
    @blp.doc(
        summary="List the caller's projects",
        operationId="list_projects",
        security=[{"bearerAuth": []}],
    )
    def get(self):
        db = SessionLocal()
        try:
            user_sub = g.user.get("sub") or ""
            projects = project_service.list_for_user(db, user_sub=user_sub)
            project_service.mark_stale_as_failed(db, projects)
            return [p.to_dict() for p in projects]
        finally:
            db.close()

    @require_auth
    @blp.response(201, ProjectCreateResponse)
    @blp.doc(
        summary="Upload a media file and queue transcription",
        operationId="create_project",
        security=[{"bearerAuth": []}],
        requestBody={
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {
                            "file": {"type": "string", "format": "binary"},
                            "language": {"type": "string"},
                        },
                    }
                }
            },
        },
    )
    def post(self):
        user_sub = g.user.get("sub") or ""
        if not user_sub:
            abort(401, message="Invalid user claims")
        if not settings.s3_bucket:
            abort(500, message="S3 bucket not configured")
        if "file" not in request.files:
            abort(400, message="file is required (multipart form)")

        uploaded = request.files["file"]
        filename = _sanitize_filename(uploaded.filename or "upload.bin")
        language = (request.form.get("language") or "").strip().lower() or None

        project_id = project_service.new_project_id()
        source_key = f"{settings.s3_upload_prefix}{project_id}/{filename}"

        s3 = S3Service()
        try:
            s3.upload_fileobj(source_key, uploaded.stream, content_type=uploaded.mimetype)
        except Exception as exc:
            abort(502, message=f"S3 upload failed: {exc}")

        db = SessionLocal()
        try:
            project = project_service.create_project(
                db,
                project_id=project_id,
                user_sub=user_sub,
                original_filename=filename,
                language=language,
                source_key=source_key,
            )
            project_service.update_status(db, project=project, status=ProjectStatus.QUEUED)
            payload = {"id": project.id, "status": project.status}
        finally:
            db.close()

        # Use project_id as Celery task_id so we can revoke a running task
        # later without persisting a separate column.
        celery_app.send_task("transcribe", args=[project_id], task_id=project_id)
        return payload


@blp.route("/<string:project_id>")
class ProjectDetail(MethodView):
    @require_auth
    @blp.response(200, ProjectSummary)
    @blp.doc(
        summary="Get a single project (status + progress)",
        operationId="get_project",
        security=[{"bearerAuth": []}],
    )
    def get(self, project_id: str):
        db = SessionLocal()
        try:
            user_sub = g.user.get("sub") or ""
            project = project_service.get_for_user(
                db, project_id=project_id, user_sub=user_sub
            )
            if project is None:
                abort(404, message="Project not found")
            project_service.mark_stale_as_failed(db, [project])
            return project.to_dict()
        finally:
            db.close()

    @require_auth
    @blp.response(204)
    @blp.doc(
        summary="Delete a project and its S3 artifacts",
        operationId="delete_project",
        security=[{"bearerAuth": []}],
    )
    def delete(self, project_id: str):
        db = SessionLocal()
        try:
            user_sub = g.user.get("sub") or ""
            project = project_service.get_for_user(
                db, project_id=project_id, user_sub=user_sub
            )
            if project is None:
                abort(404, message="Project not found")
            # SIGKILL because a stuck task is often blocked inside a C-level
            # socket read (e.g. boto3 download) which won't respond to SIGTERM.
            # Revoke is a no-op for tasks that already finished.
            try:
                celery_app.control.revoke(
                    project_id, terminate=True, signal="SIGKILL"
                )
            except Exception:
                pass
            s3 = S3Service()
            if project.source_key:
                s3.delete(project.source_key)
            if project.srt_key:
                s3.delete(project.srt_key)
            project_service.delete_project(db, project=project)
            return ""
        finally:
            db.close()


@blp.route("/<string:project_id>/srt")
class ProjectSrt(MethodView):
    @require_auth
    @blp.response(200, PresignedUrlResponse)
    @blp.doc(
        summary="Get a time-limited download URL for the SRT",
        operationId="get_project_srt",
        security=[{"bearerAuth": []}],
    )
    def get(self, project_id: str):
        db = SessionLocal()
        try:
            user_sub = g.user.get("sub") or ""
            project = project_service.get_for_user(
                db, project_id=project_id, user_sub=user_sub
            )
            if project is None:
                abort(404, message="Project not found")
            if not project.srt_key:
                abort(409, message="SRT is not ready yet")
            s3 = S3Service()
            return {"url": s3.presign_get(project.srt_key)}
        finally:
            db.close()
