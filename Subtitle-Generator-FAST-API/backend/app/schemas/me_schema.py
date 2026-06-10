from pydantic import BaseModel


class MeResponse(BaseModel):
    sub: str
    username: str | None = None
    email: str | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    email_verified: bool | None = None
    roles: list[str] = []
