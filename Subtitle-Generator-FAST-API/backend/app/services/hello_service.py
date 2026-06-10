from app.schemas.hello_schema import HelloResponse


class HelloService:
    def get_greeting(self) -> HelloResponse:
        return HelloResponse(message="hello world")
