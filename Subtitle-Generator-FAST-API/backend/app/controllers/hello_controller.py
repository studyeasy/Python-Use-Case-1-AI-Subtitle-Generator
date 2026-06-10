from fastapi import APIRouter, Depends

from app.schemas.hello_schema import HelloResponse
from app.services.hello_service import HelloService

router = APIRouter(prefix="/hello", tags=["Greetings"])


def get_hello_service() -> HelloService:
    return HelloService()


@router.get(
    "",
    response_model=HelloResponse,
    summary="Hello World",
    operation_id="hello_world",
)
def hello_world(
    service: HelloService = Depends(get_hello_service),
) -> HelloResponse:
    return service.get_greeting()
