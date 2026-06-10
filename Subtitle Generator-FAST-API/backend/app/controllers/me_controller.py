from typing import Any

from fastapi import APIRouter, Depends

from app.auth.cognito import claims_to_roles, get_current_user
from app.schemas.me_schema import MeResponse

router = APIRouter(prefix="/me", tags=["Auth"])


@router.get(
    "",
    response_model=MeResponse,
    summary="Current user",
    operation_id="get_me",
)
def get_me(claims: dict[str, Any] = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        sub=claims.get("sub", ""),
        username=claims.get("username") or claims.get("cognito:username"),
        email=claims.get("email"),
        name=claims.get("name"),
        given_name=claims.get("given_name"),
        family_name=claims.get("family_name"),
        email_verified=claims.get("email_verified"),
        roles=claims_to_roles(claims),
    )
