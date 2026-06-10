"""Auth endpoints under /auth — the only Cognito entrypoint the frontend has."""

from flask import g
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.auth import require_auth
from app.schemas.auth_schema import (
    ConfirmSignupRequest,
    ConfirmSignupResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RegisterRequest,
    RegisterResponse,
    ResendCodeRequest,
    ResendCodeResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
)
from app.schemas.me_schema import MeResponse
from app.services.cognito_service import (
    CognitoError,
    claims_to_roles,
    cognito_service,
)

blp = Blueprint("Auth", __name__, description="Authentication endpoints")


def _cognito_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except CognitoError as exc:
        abort(exc.status_code, message=exc.detail)


@blp.route("/register")
class Register(MethodView):
    @blp.arguments(RegisterRequest)
    @blp.response(201, RegisterResponse)
    @blp.doc(summary="Register a new user via AWS Cognito", operationId="auth_register")
    def post(self, body):
        result = _cognito_call(
            cognito_service.register,
            email=body["email"],
            password=body["password"],
            first_name=body.get("first_name"),
            last_name=body.get("last_name"),
        )
        confirmed = result.get("confirmed")
        message = (
            "User registered"
            if confirmed
            else "User registered. Confirm the account before logging in."
        )
        return {"ok": True, "message": message, "confirmed": confirmed}


@blp.route("/confirm")
class ConfirmSignup(MethodView):
    @blp.arguments(ConfirmSignupRequest)
    @blp.response(200, ConfirmSignupResponse)
    @blp.doc(
        summary="Confirm a newly registered user with the emailed code",
        operationId="auth_confirm",
    )
    def post(self, body):
        _cognito_call(
            cognito_service.confirm_sign_up,
            email=body["email"],
            code=body["code"],
        )
        return {"ok": True, "confirmed": True, "message": "User confirmed"}


@blp.route("/resend-confirmation")
class ResendConfirmation(MethodView):
    @blp.arguments(ResendCodeRequest)
    @blp.response(200, ResendCodeResponse)
    @blp.doc(
        summary="Resend the Cognito confirmation code to the user's email",
        operationId="auth_resend_confirmation",
    )
    def post(self, body):
        _cognito_call(cognito_service.resend_confirmation_code, email=body["email"])
        return {"ok": True, "message": "Confirmation code sent"}


@blp.route("/forgot-password")
class ForgotPassword(MethodView):
    @blp.arguments(ForgotPasswordRequest)
    @blp.response(200, ForgotPasswordResponse)
    @blp.doc(
        summary="Send a password reset code to the user's email",
        operationId="auth_forgot_password",
    )
    def post(self, body):
        _cognito_call(cognito_service.forgot_password, email=body["email"])
        return {"ok": True, "message": "Password reset code sent"}


@blp.route("/reset-password")
class ResetPassword(MethodView):
    @blp.arguments(ResetPasswordRequest)
    @blp.response(200, ResetPasswordResponse)
    @blp.doc(
        summary="Reset the password using the emailed code",
        operationId="auth_reset_password",
    )
    def post(self, body):
        _cognito_call(
            cognito_service.confirm_forgot_password,
            email=body["email"],
            code=body["code"],
            new_password=body["new_password"],
        )
        return {"ok": True, "message": "Password reset"}


@blp.route("/login")
class Login(MethodView):
    @blp.arguments(LoginRequest)
    @blp.response(200, TokenResponse)
    @blp.doc(
        summary="Exchange credentials for Cognito tokens",
        operationId="auth_login",
    )
    def post(self, body):
        tokens = _cognito_call(cognito_service.login, body["email"], body["password"])
        return {
            "access_token": tokens["access_token"],
            "id_token": tokens.get("id_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in"),
            "refresh_expires_in": tokens.get("refresh_expires_in"),
            "token_type": tokens.get("token_type", "Bearer"),
        }


@blp.route("/logout")
class Logout(MethodView):
    @blp.arguments(LogoutRequest)
    @blp.response(200, LogoutResponse)
    @blp.doc(
        summary="Revoke the current Cognito refresh token",
        operationId="auth_logout",
    )
    def post(self, body):
        _cognito_call(cognito_service.logout, body["refresh_token"])
        return {"ok": True}


@blp.route("/me")
class Me(MethodView):
    @require_auth
    @blp.response(200, MeResponse)
    @blp.doc(
        summary="Decode the caller's Cognito access token",
        operationId="auth_me",
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
