from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint

from app.auth import require_auth
from app.schemas.me_schema import MeResponse
from app.services.cognito_service import claims_to_roles

blp = Blueprint("Me", __name__, description="Information about the logged-in user")


@blp.route("")
class MeController(MethodView):
    @require_auth
    @blp.response(200, MeResponse)
    @blp.doc(
        summary="Current user",
        operationId="get_me",
        security=[{"bearerAuth": []}],
    )
    def get(self):
        claims = g.user
        return {
            "sub": claims.get("sub", ""),
            "username": claims.get("username") or claims.get("cognito:username"),
            "email": claims.get("email"),
            "name": claims.get("name"),
            "given_name": claims.get("given_name"),
            "family_name": claims.get("family_name"),
            "email_verified": claims.get("email_verified"),
            "roles": claims_to_roles(claims),
        }
