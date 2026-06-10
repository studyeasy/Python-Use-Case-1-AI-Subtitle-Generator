from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from myapp.services.cognito_service import CognitoClientError, cognito_client
from myapp.utils.schemas import (
    ConfirmSignupRequest,
    ConfirmSignupResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    ResendCodeRequest,
    ResendCodeResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
)


# ----------------------------------------------------------------------- auth


@extend_schema(
    summary="Register a new user via AWS Cognito",
    operation_id="auth_register",
    tags=["Auth"],
    request=RegisterRequest,
    responses={201: RegisterResponse},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def register(request):
    body = RegisterRequest(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    try:
        result = cognito_client.register(
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name") or None,
            last_name=data.get("last_name") or None,
        )
    except CognitoClientError as e:
        return Response({"detail": e.detail}, status=e.status_code)
    confirmed = result.get("confirmed")
    message = (
        "User registered"
        if confirmed
        else "User registered. Confirm the account before logging in."
    )
    return Response(
        {"ok": True, "message": message, "confirmed": confirmed},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    summary="Confirm a newly registered user with the emailed code",
    operation_id="auth_confirm",
    tags=["Auth"],
    request=ConfirmSignupRequest,
    responses={200: ConfirmSignupResponse},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def confirm(request):
    body = ConfirmSignupRequest(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    try:
        cognito_client.confirm_sign_up(email=data["email"], code=data["code"])
    except CognitoClientError as e:
        return Response({"detail": e.detail}, status=e.status_code)
    return Response({"ok": True, "confirmed": True, "message": "User confirmed"})


@extend_schema(
    summary="Resend the Cognito confirmation code to the user's email",
    operation_id="auth_resend_confirmation",
    tags=["Auth"],
    request=ResendCodeRequest,
    responses={200: ResendCodeResponse},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def resend_confirmation(request):
    body = ResendCodeRequest(data=request.data)
    body.is_valid(raise_exception=True)
    try:
        cognito_client.resend_confirmation_code(
            email=body.validated_data["email"]
        )
    except CognitoClientError as e:
        return Response({"detail": e.detail}, status=e.status_code)
    return Response({"ok": True, "message": "Confirmation code sent"})


@extend_schema(
    summary="Send a password reset code to the user's email",
    operation_id="auth_forgot_password",
    tags=["Auth"],
    request=ForgotPasswordRequest,
    responses={200: ForgotPasswordResponse},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def forgot_password(request):
    body = ForgotPasswordRequest(data=request.data)
    body.is_valid(raise_exception=True)
    try:
        cognito_client.forgot_password(email=body.validated_data["email"])
    except CognitoClientError as e:
        return Response({"detail": e.detail}, status=e.status_code)
    return Response({"ok": True, "message": "Password reset code sent"})


@extend_schema(
    summary="Reset the password using the emailed code",
    operation_id="auth_reset_password",
    tags=["Auth"],
    request=ResetPasswordRequest,
    responses={200: ResetPasswordResponse},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def reset_password(request):
    body = ResetPasswordRequest(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    try:
        cognito_client.confirm_forgot_password(
            email=data["email"],
            code=data["code"],
            new_password=data["new_password"],
        )
    except CognitoClientError as e:
        return Response({"detail": e.detail}, status=e.status_code)
    return Response({"ok": True, "message": "Password reset"})


@extend_schema(
    summary="Exchange credentials for Cognito tokens",
    operation_id="auth_login",
    tags=["Auth"],
    request=LoginRequest,
    responses={200: TokenResponse},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    body = LoginRequest(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    try:
        tokens = cognito_client.login(data["email"], data["password"])
    except CognitoClientError as e:
        return Response({"detail": e.detail}, status=e.status_code)
    return Response(
        {
            "access_token": tokens["access_token"],
            "id_token": tokens.get("id_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in"),
            "refresh_expires_in": tokens.get("refresh_expires_in"),
            "token_type": tokens.get("token_type", "Bearer"),
        }
    )


@extend_schema(
    summary="Revoke the current Cognito refresh token",
    operation_id="auth_logout",
    tags=["Auth"],
    request=LogoutRequest,
    responses={200: LogoutResponse},
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def logout(request):
    body = LogoutRequest(data=request.data)
    body.is_valid(raise_exception=True)
    try:
        cognito_client.logout(body.validated_data["refresh_token"])
    except CognitoClientError as e:
        return Response({"detail": e.detail}, status=e.status_code)
    return Response({"ok": True})


@extend_schema(
    summary="Decode the caller's Cognito access token",
    operation_id="get_me",
    tags=["Auth"],
    responses={200: MeResponse},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response(
        {
            "sub": user.sub,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "given_name": user.given_name,
            "family_name": user.family_name,
            "email_verified": user.email_verified,
            "roles": user.roles,
        }
    )
