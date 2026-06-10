from flask.views import MethodView
from flask_smorest import Blueprint

from app.auth import require_auth
from app.schemas.hello_schema import HelloResponse
from app.services.hello_service import HelloService

blp = Blueprint("Greetings", __name__, description="")


@blp.route("")
class HelloController(MethodView):
    def __init__(self) -> None:
        self.service = HelloService()

    @require_auth
    @blp.response(200, HelloResponse)
    @blp.doc(
        summary="Hello World",
        operationId="hello_world",
        security=[{"bearerAuth": []}],
    )
    def get(self):
        return self.service.get_greeting()
