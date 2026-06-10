from pathlib import PurePosixPath

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mywebsite.celery import app as celery_app

from myapp.models.project import Project, ProjectStatus, mark_stale_as_failed
from myapp.services.s3_service import S3Service
from myapp.utils.schemas import (
    PresignedUrlResponse,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectSummary,
)


def _sanitize_filename(name: str) -> str:
    base = PurePosixPath(name.replace("\\", "/")).name
    return base or "upload.bin"


def _create(request):
    if "file" not in request.FILES:
        return Response({"detail": "file is required"}, status=400)
    uploaded = request.FILES["file"]
    language = (request.data.get("language") or "").strip().lower() or None

    if not settings.S3["BUCKET"]:
        return Response({"detail": "S3 bucket not configured"}, status=500)

    user_sub = request.user.sub
    filename = _sanitize_filename(uploaded.name or "upload.bin")

    project = Project.objects.create(
        user_sub=user_sub,
        original_filename=filename,
        language=language,
        status=ProjectStatus.PENDING,
        source_key="",
    )
    source_key = f"{settings.S3['UPLOAD_PREFIX']}{project.id}/{filename}"

    s3 = S3Service()
    try:
        s3.upload_fileobj(source_key, uploaded, content_type=uploaded.content_type)
    except Exception as exc:
        project.delete()
        return Response({"detail": f"S3 upload failed: {exc}"}, status=502)

    project.source_key = source_key
    project.status = ProjectStatus.QUEUED
    project.save(update_fields=["source_key", "status", "updated_at"])

    # Use project.id as Celery task_id so we can revoke a running task later
    # without persisting a separate column.
    celery_app.send_task("transcribe", args=[project.id], task_id=project.id)

    return Response({"id": project.id, "status": project.status}, status=201)


def _list(request):
    user_sub = request.user.sub
    projects = list(Project.objects.filter(user_sub=user_sub))
    mark_stale_as_failed(projects)
    return Response([p.to_dict() for p in projects])


@extend_schema(
    methods=["POST"],
    summary="Upload a media file and queue transcription",
    operation_id="create_project",
    tags=["Projects"],
    request=ProjectCreateRequest,
    responses={201: ProjectCreateResponse},
)
@extend_schema(
    methods=["GET"],
    summary="List the caller's projects",
    operation_id="list_projects",
    tags=["Projects"],
    responses={200: ProjectSummary(many=True)},
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def projects_collection(request):
    if request.method == "POST":
        return _create(request)
    return _list(request)


@extend_schema(
    methods=["GET"],
    summary="Get a single project",
    operation_id="get_project",
    tags=["Projects"],
    responses={200: ProjectSummary},
)
@extend_schema(
    methods=["DELETE"],
    summary="Delete a project and its S3 artifacts",
    operation_id="delete_project",
    tags=["Projects"],
    responses={204: None},
)
@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def project_detail(request, project_id: str):
    user_sub = request.user.sub
    project = Project.objects.filter(pk=project_id, user_sub=user_sub).first()
    if project is None:
        return Response({"detail": "Project not found"}, status=404)

    if request.method == "DELETE":
        # SIGKILL because a stuck task is often blocked inside a C-level socket
        # read (e.g. boto3 download) which won't respond to SIGTERM. Revoke is
        # a no-op for tasks that already finished.
        try:
            celery_app.control.revoke(
                project.id, terminate=True, signal="SIGKILL"
            )
        except Exception:
            pass
        s3 = S3Service()
        if project.source_key:
            s3.delete(project.source_key)
        if project.srt_key:
            s3.delete(project.srt_key)
        project.delete()
        return Response(status=204)

    mark_stale_as_failed([project])
    return Response(project.to_dict())


@extend_schema(
    summary="Get a presigned download URL for the SRT",
    operation_id="get_project_srt",
    tags=["Projects"],
    responses={200: PresignedUrlResponse},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_srt(request, project_id: str):
    user_sub = request.user.sub
    project = Project.objects.filter(pk=project_id, user_sub=user_sub).first()
    if project is None:
        return Response({"detail": "Project not found"}, status=404)
    if not project.srt_key:
        return Response({"detail": "SRT is not ready yet"}, status=409)
    s3 = S3Service()
    return Response({"url": s3.presign_get(project.srt_key)})
