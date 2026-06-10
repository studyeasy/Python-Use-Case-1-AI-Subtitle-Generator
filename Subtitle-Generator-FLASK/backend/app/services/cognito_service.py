"""AWS Cognito integration for the Flask backend.

The frontend talks only to this backend. This module brokers Cognito
registration, login, logout, and JWT validation for protected API routes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.request
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from jose import JWTError, jwt

from app.config import settings


class CognitoError(Exception):
    """Raised when a Cognito call fails. Carries an HTTP status."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


_cognito_client: Any | None = None
_jwks_cache: dict[str, Any] | None = None
_jwks_fetched_at: float = 0.0
_jwks_ttl_seconds = 3600


def _get_cognito_client() -> Any:
    global _cognito_client
    if _cognito_client is None:
        _cognito_client = boto3.client(
            "cognito-idp",
            region_name=settings.aws_region,
        )
    return _cognito_client


def _client_secret() -> str | None:
    secret = settings.cognito_app_client_secret
    return secret.strip() if secret and secret.strip() else None


def _secret_hash(username: str) -> str | None:
    secret = _client_secret()
    if not secret:
        return None
    digest = hmac.new(
        secret.encode("utf-8"),
        f"{username}{settings.cognito_app_client_id}".encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def _auth_parameters(username: str, password: str | None = None) -> dict[str, str]:
    params = {"USERNAME": username}
    if password is not None:
        params["PASSWORD"] = password
    secret_hash = _secret_hash(username)
    if secret_hash:
        params["SECRET_HASH"] = secret_hash
    return params


def _map_cognito_error(exc: ClientError, fallback: str) -> CognitoError:
    error = exc.response.get("Error", {})
    code = error.get("Code", "")
    message = error.get("Message") or fallback

    if code in {"NotAuthorizedException", "UserNotFoundException"}:
        return CognitoError(401, "Invalid username or password")
    if code in {"UsernameExistsException", "AliasExistsException"}:
        return CognitoError(409, "User exists with same email")
    if code == "UserNotConfirmedException":
        return CognitoError(
            403, "User is not confirmed. Confirm the account before logging in."
        )
    if code in {
        "CodeMismatchException",
        "ExpiredCodeException",
        "InvalidPasswordException",
        "InvalidParameterException",
        "LimitExceededException",
        "PasswordResetRequiredException",
        "TooManyRequestsException",
    }:
        return CognitoError(400, message)
    return CognitoError(502, f"{fallback}: {message}")


def _load_jwks(force_refresh: bool = False) -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at
    now = time.time()
    if (
        not force_refresh
        and _jwks_cache is not None
        and (now - _jwks_fetched_at) < _jwks_ttl_seconds
    ):
        return _jwks_cache

    try:
        with urllib.request.urlopen(settings.cognito_jwks_url, timeout=10) as response:
            _jwks_cache = json.loads(response.read().decode("utf-8"))
            _jwks_fetched_at = now
            return _jwks_cache
    except Exception as exc:
        raise CognitoError(503, "Could not fetch Cognito JWKS") from exc


def _find_jwk(token: str) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise CognitoError(401, "Invalid token header") from exc

    kid = header.get("kid")
    jwks = _load_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    jwks = _load_jwks(force_refresh=True)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise CognitoError(401, "Token signing key not found")


def claims_to_roles(claims: dict[str, Any]) -> list[str]:
    groups = claims.get(settings.cognito_groups_claim, [])
    if isinstance(groups, list):
        return [str(group) for group in groups]
    if isinstance(groups, str):
        return [groups]
    return []


class CognitoService:
    """Validates Cognito access tokens + brokers register/login/logout."""

    # ------------------------------------------------------------ JWT validation
    def decode(self, token: str) -> dict[str, Any]:
        key = _find_jwk(token)
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=settings.cognito_issuer,
                options={"verify_aud": False},
            )
        except JWTError as exc:
            raise CognitoError(401, f"Invalid or expired token: {exc}") from exc

        token_use = claims.get("token_use")
        if token_use != settings.cognito_token_use:
            raise CognitoError(401, f"Invalid token_use: {token_use}")

        client_id = claims.get("client_id") or claims.get("aud")
        if client_id != settings.cognito_app_client_id:
            raise CognitoError(401, "Invalid Cognito app client")

        return claims

    def merge_user_attributes(
        self, claims: dict[str, Any], access_token: str
    ) -> dict[str, Any]:
        """Enrich the JWT claims with Cognito GetUser attributes when possible."""
        try:
            response = _get_cognito_client().get_user(AccessToken=access_token)
        except (ClientError, BotoCoreError):
            return claims

        merged = dict(claims)
        for attribute in response.get("UserAttributes", []):
            name = attribute.get("Name")
            value = attribute.get("Value")
            if name and value is not None:
                merged[name] = value
        merged.setdefault("username", response.get("Username"))
        return merged

    # ----------------------------------------------------------------- login
    def login(self, username: str, password: str) -> dict[str, Any]:
        try:
            response = _get_cognito_client().initiate_auth(
                ClientId=settings.cognito_app_client_id,
                AuthFlow=settings.cognito_auth_flow,
                AuthParameters=_auth_parameters(username, password),
            )
        except ClientError as exc:
            raise _map_cognito_error(exc, "Login failed") from exc
        except BotoCoreError as exc:
            raise CognitoError(502, f"Login failed: {exc}") from exc

        challenge = response.get("ChallengeName")
        if challenge:
            raise CognitoError(403, f"Cognito challenge required: {challenge}")

        auth = response.get("AuthenticationResult") or {}
        return {
            "access_token": auth.get("AccessToken"),
            "id_token": auth.get("IdToken"),
            "refresh_token": auth.get("RefreshToken"),
            "expires_in": auth.get("ExpiresIn"),
            "refresh_expires_in": None,
            "token_type": auth.get("TokenType", "Bearer"),
        }

    # ---------------------------------------------------------------- logout
    def logout(self, refresh_token: str) -> None:
        try:
            kwargs: dict[str, Any] = {
                "ClientId": settings.cognito_app_client_id,
                "Token": refresh_token,
            }
            secret = _client_secret()
            if secret:
                kwargs["ClientSecret"] = secret
            _get_cognito_client().revoke_token(**kwargs)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in {"InvalidParameterException", "NotAuthorizedException"}:
                return
            raise _map_cognito_error(exc, "Logout failed") from exc
        except BotoCoreError as exc:
            raise CognitoError(502, f"Logout failed: {exc}") from exc

    # -------------------------------------------------------------- register
    def register(
        self,
        *,
        email: str,
        password: str,
        first_name: str | None,
        last_name: str | None,
    ) -> dict[str, Any]:
        attributes = [{"Name": "email", "Value": email}]
        if first_name:
            attributes.append({"Name": "given_name", "Value": first_name})
        if last_name:
            attributes.append({"Name": "family_name", "Value": last_name})

        kwargs: dict[str, Any] = {
            "ClientId": settings.cognito_app_client_id,
            "Username": email,
            "Password": password,
            "UserAttributes": attributes,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            response = _get_cognito_client().sign_up(**kwargs)
            confirmed = bool(response.get("UserConfirmed"))
            if settings.cognito_auto_confirm_sign_up and not confirmed:
                _get_cognito_client().admin_confirm_sign_up(
                    UserPoolId=settings.cognito_user_pool_id,
                    Username=email,
                )
                _get_cognito_client().admin_update_user_attributes(
                    UserPoolId=settings.cognito_user_pool_id,
                    Username=email,
                    UserAttributes=[{"Name": "email_verified", "Value": "true"}],
                )
                confirmed = True
            return {"confirmed": confirmed}
        except ClientError as exc:
            raise _map_cognito_error(exc, "Could not register user") from exc
        except BotoCoreError as exc:
            raise CognitoError(502, f"Could not register user: {exc}") from exc

    # --------------------------------------------------------- confirm sign up
    def confirm_sign_up(self, email: str, code: str) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.cognito_app_client_id,
            "Username": email,
            "ConfirmationCode": code,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            _get_cognito_client().confirm_sign_up(**kwargs)
        except ClientError as exc:
            raise _map_cognito_error(exc, "Could not confirm user") from exc
        except BotoCoreError as exc:
            raise CognitoError(502, f"Could not confirm user: {exc}") from exc

    # --------------------------------------------------- resend confirmation
    def resend_confirmation_code(self, email: str) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.cognito_app_client_id,
            "Username": email,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            _get_cognito_client().resend_confirmation_code(**kwargs)
        except ClientError as exc:
            raise _map_cognito_error(
                exc, "Could not resend confirmation code"
            ) from exc
        except BotoCoreError as exc:
            raise CognitoError(
                502, f"Could not resend confirmation code: {exc}"
            ) from exc

    # --------------------------------------------------------- forgot password
    def forgot_password(self, email: str) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.cognito_app_client_id,
            "Username": email,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            _get_cognito_client().forgot_password(**kwargs)
        except ClientError as exc:
            raise _map_cognito_error(
                exc, "Could not start password reset"
            ) from exc
        except BotoCoreError as exc:
            raise CognitoError(
                502, f"Could not start password reset: {exc}"
            ) from exc

    # ------------------------------------------------ confirm forgot password
    def confirm_forgot_password(
        self, email: str, code: str, new_password: str
    ) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.cognito_app_client_id,
            "Username": email,
            "ConfirmationCode": code,
            "Password": new_password,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            _get_cognito_client().confirm_forgot_password(**kwargs)
        except ClientError as exc:
            raise _map_cognito_error(exc, "Could not reset password") from exc
        except BotoCoreError as exc:
            raise CognitoError(
                502, f"Could not reset password: {exc}"
            ) from exc


cognito_service = CognitoService()
