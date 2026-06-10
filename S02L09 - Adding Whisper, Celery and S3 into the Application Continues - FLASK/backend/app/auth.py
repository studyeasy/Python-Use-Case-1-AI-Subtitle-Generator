from functools import wraps
from typing import Any, Callable

from flask import g, request
from flask_smorest import abort

from app.services.cognito_service import CognitoError, cognito_service


def _extract_bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    return header.split(" ", 1)[1].strip() or None


def require_auth(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that validates a Cognito Bearer token and stores the
    decoded claims (enriched with Cognito user attributes) on ``flask.g.user``."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token = _extract_bearer_token()
        if not token:
            abort(401, message="Missing Bearer token")
        try:
            claims = cognito_service.decode(token)
            claims = cognito_service.merge_user_attributes(claims, token)
        except CognitoError as exc:
            abort(exc.status_code, message=exc.detail)
        except Exception as exc:  # noqa: BLE001
            abort(401, message=f"Token validation failed: {exc}")
        g.user = claims
        return fn(*args, **kwargs)

    return wrapper
