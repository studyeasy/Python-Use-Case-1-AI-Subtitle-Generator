from drf_spectacular.utils import extend_schema
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from myapp.utils.schemas import HealthResponse, HelloResponse


@extend_schema(
    summary="Hello World",
    operation_id="hello_world",
    tags=["Greetings"],
    responses={200: HelloResponse},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def hello_world(request):
    return Response({"message": "hello world"})


@extend_schema(
    summary="Health check",
    operation_id="health",
    tags=["System"],
    responses={200: HealthResponse},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})
