"""Auth endpoints exposed under /auth.

The frontend calls these directly; Cognito stays behind the backend boundary.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.cognito import claims_to_roles, cognito_client, get_current_user
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

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user via AWS Cognito",
)
async def register(body: RegisterRequest) -> RegisterResponse:
    result = await cognito_client.register(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    confirmed = result.get("confirmed")
    message = (
        "User registered"
        if confirmed
        else "User registered. Confirm the account before logging in."
    )
    return RegisterResponse(message=message, confirmed=confirmed)


@router.post(
    "/confirm",
    response_model=ConfirmSignupResponse,
    summary="Confirm a newly registered user with the emailed code",
)
async def confirm(body: ConfirmSignupRequest) -> ConfirmSignupResponse:
    await cognito_client.confirm_sign_up(email=body.email, code=body.code)
    return ConfirmSignupResponse()


@router.post(
    "/resend-confirmation",
    response_model=ResendCodeResponse,
    summary="Resend the Cognito confirmation code to the user's email",
)
async def resend_confirmation(body: ResendCodeRequest) -> ResendCodeResponse:
    await cognito_client.resend_confirmation_code(email=body.email)
    return ResendCodeResponse()


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Send a password reset code to the user's email",
)
async def forgot_password(body: ForgotPasswordRequest) -> ForgotPasswordResponse:
    await cognito_client.forgot_password(email=body.email)
    return ForgotPasswordResponse()


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset the password using the emailed code",
)
async def reset_password(body: ResetPasswordRequest) -> ResetPasswordResponse:
    await cognito_client.confirm_forgot_password(
        email=body.email,
        code=body.code,
        new_password=body.new_password,
    )
    return ResetPasswordResponse()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Exchange credentials for Cognito tokens",
)
async def login(body: LoginRequest) -> TokenResponse:
    tokens = await cognito_client.login(body.email, body.password)
    return TokenResponse(
        access_token=tokens["access_token"],
        id_token=tokens.get("id_token"),
        refresh_token=tokens.get("refresh_token"),
        expires_in=tokens.get("expires_in"),
        refresh_expires_in=tokens.get("refresh_expires_in"),
        token_type=tokens.get("token_type", "Bearer"),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Revoke the current Cognito refresh token",
)
async def logout(body: LogoutRequest | None = None) -> LogoutResponse:
    if body is None or not body.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required",
        )
    await cognito_client.logout(body.refresh_token)
    return LogoutResponse(ok=True)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Decode the caller's Cognito access token",
)
def me(claims: dict[str, Any] = Depends(get_current_user)) -> MeResponse:
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
