"""AWS Cognito integration for the Django backend.

This module exposes:

* ``CognitoAuthentication`` — DRF auth class that validates Bearer JWTs against
  the Cognito User Pool's JWKS.
* ``CognitoClient``         — login / logout / register broker (boto3).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from jose import JWTError, jwt
from rest_framework import authentication, exceptions


@dataclass
class CognitoUser:
    sub: str
    username: str
    email: str
    name: str
    given_name: str
    family_name: str
    email_verified: bool
    roles: list[str]
    claims: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return True


# ----------------------------------------------------------------- SDK clients
_cognito_client: Any | None = None
_jwks_cache: dict[str, Any] | None = None
_jwks_fetched_at: float = 0.0
_jwks_ttl_seconds = 3600


def _get_cognito_client() -> Any:
    global _cognito_client
    if _cognito_client is None:
        _cognito_client = boto3.client(
            "cognito-idp",
            region_name=settings.COGNITO["REGION"],
        )
    return _cognito_client


def _client_secret() -> str | None:
    secret = settings.COGNITO.get("APP_CLIENT_SECRET")
    return secret.strip() if secret and secret.strip() else None


def _secret_hash(username: str) -> str | None:
    secret = _client_secret()
    if not secret:
        return None
    digest = hmac.new(
        secret.encode("utf-8"),
        f"{username}{settings.COGNITO['APP_CLIENT_ID']}".encode("utf-8"),
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


def _issuer() -> str:
    override = settings.COGNITO.get("ISSUER_OVERRIDE")
    if override:
        return override.rstrip("/")
    return (
        f"https://cognito-idp.{settings.COGNITO['REGION']}.amazonaws.com/"
        f"{settings.COGNITO['USER_POOL_ID']}"
    )


def _jwks_url() -> str:
    override = settings.COGNITO.get("JWKS_URL_OVERRIDE")
    if override:
        return override
    return f"{_issuer()}/.well-known/jwks.json"


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
        with urllib.request.urlopen(_jwks_url(), timeout=10) as response:
            _jwks_cache = json.loads(response.read().decode("utf-8"))
            _jwks_fetched_at = now
            return _jwks_cache
    except Exception as exc:
        raise CognitoClientError(503, "Could not fetch Cognito JWKS") from exc


def _find_jwk(token: str) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise CognitoClientError(401, "Invalid token header") from exc

    kid = header.get("kid")
    jwks = _load_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    jwks = _load_jwks(force_refresh=True)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise CognitoClientError(401, "Token signing key not found")


def _claims_to_roles(claims: dict[str, Any]) -> list[str]:
    groups = claims.get(settings.COGNITO.get("GROUPS_CLAIM", "cognito:groups"), [])
    if isinstance(groups, list):
        return [str(group) for group in groups]
    if isinstance(groups, str):
        return [groups]
    return []


# --------------------------------------------------------------- JWT validation


class CognitoAuthentication(authentication.BaseAuthentication):
    """DRF auth class that validates Cognito-issued access tokens."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header.")

        token = auth[1].decode()
        try:
            key = _find_jwk(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=_issuer(),
                options={"verify_aud": False},
            )
        except JWTError as exc:
            raise exceptions.AuthenticationFailed(f"Invalid or expired token: {exc}")
        except CognitoClientError as exc:
            raise exceptions.AuthenticationFailed(exc.detail)

        expected_token_use = settings.COGNITO.get("TOKEN_USE", "access")
        if claims.get("token_use") != expected_token_use:
            raise exceptions.AuthenticationFailed(
                f"Invalid token_use: {claims.get('token_use')}"
            )

        client_id = claims.get("client_id") or claims.get("aud")
        if client_id != settings.COGNITO["APP_CLIENT_ID"]:
            raise exceptions.AuthenticationFailed("Invalid Cognito app client.")

        # Enrich claims with Cognito GetUser attributes when the token permits.
        try:
            response = _get_cognito_client().get_user(AccessToken=token)
            for attribute in response.get("UserAttributes", []):
                name = attribute.get("Name")
                value = attribute.get("Value")
                if name and value is not None:
                    claims.setdefault(name, value)
            claims.setdefault("username", response.get("Username"))
        except (ClientError, BotoCoreError):
            pass

        user = CognitoUser(
            sub=claims.get("sub", ""),
            username=claims.get("username") or claims.get("cognito:username") or "",
            email=claims.get("email", ""),
            name=claims.get("name", ""),
            given_name=claims.get("given_name", ""),
            family_name=claims.get("family_name", ""),
            email_verified=bool(claims.get("email_verified", False)),
            roles=_claims_to_roles(claims),
            claims=claims,
        )
        return (user, token)

    def authenticate_header(self, request):
        return self.keyword


# ----------------------------------------------- broker (login / logout / register)


class CognitoClientError(Exception):
    """Raised when a Cognito call fails. Carries an HTTP status."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _map_cognito_error(exc: ClientError, fallback: str) -> CognitoClientError:
    error = exc.response.get("Error", {})
    code = error.get("Code", "")
    message = error.get("Message") or fallback

    if code in {"NotAuthorizedException", "UserNotFoundException"}:
        return CognitoClientError(401, "Invalid username or password")
    if code in {"UsernameExistsException", "AliasExistsException"}:
        return CognitoClientError(409, "User exists with same email")
    if code == "UserNotConfirmedException":
        return CognitoClientError(
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
        return CognitoClientError(400, message)
    return CognitoClientError(502, f"{fallback}: {message}")


class CognitoClient:
    @staticmethod
    def login(username: str, password: str) -> dict[str, Any]:
        try:
            response = _get_cognito_client().initiate_auth(
                ClientId=settings.COGNITO["APP_CLIENT_ID"],
                AuthFlow=settings.COGNITO.get("AUTH_FLOW", "USER_PASSWORD_AUTH"),
                AuthParameters=_auth_parameters(username, password),
            )
        except ClientError as exc:
            raise _map_cognito_error(exc, "Login failed")
        except BotoCoreError as exc:
            raise CognitoClientError(502, f"Login failed: {exc}")

        challenge = response.get("ChallengeName")
        if challenge:
            raise CognitoClientError(403, f"Cognito challenge required: {challenge}")

        auth = response.get("AuthenticationResult") or {}
        return {
            "access_token": auth.get("AccessToken"),
            "id_token": auth.get("IdToken"),
            "refresh_token": auth.get("RefreshToken"),
            "expires_in": auth.get("ExpiresIn"),
            "refresh_expires_in": None,
            "token_type": auth.get("TokenType", "Bearer"),
        }

    @staticmethod
    def logout(refresh_token: str) -> None:
        try:
            kwargs: dict[str, Any] = {
                "ClientId": settings.COGNITO["APP_CLIENT_ID"],
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
            raise _map_cognito_error(exc, "Logout failed")
        except BotoCoreError as exc:
            raise CognitoClientError(502, f"Logout failed: {exc}")

    @staticmethod
    def register(
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
            "ClientId": settings.COGNITO["APP_CLIENT_ID"],
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
            if settings.COGNITO.get("AUTO_CONFIRM_SIGN_UP") and not confirmed:
                _get_cognito_client().admin_confirm_sign_up(
                    UserPoolId=settings.COGNITO["USER_POOL_ID"],
                    Username=email,
                )
                _get_cognito_client().admin_update_user_attributes(
                    UserPoolId=settings.COGNITO["USER_POOL_ID"],
                    Username=email,
                    UserAttributes=[{"Name": "email_verified", "Value": "true"}],
                )
                confirmed = True
            return {"confirmed": confirmed}
        except ClientError as exc:
            raise _map_cognito_error(exc, "Could not register user")
        except BotoCoreError as exc:
            raise CognitoClientError(502, f"Could not register user: {exc}")

    @staticmethod
    def confirm_sign_up(email: str, code: str) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.COGNITO["APP_CLIENT_ID"],
            "Username": email,
            "ConfirmationCode": code,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            _get_cognito_client().confirm_sign_up(**kwargs)
        except ClientError as exc:
            raise _map_cognito_error(exc, "Could not confirm user")
        except BotoCoreError as exc:
            raise CognitoClientError(502, f"Could not confirm user: {exc}")

    @staticmethod
    def resend_confirmation_code(email: str) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.COGNITO["APP_CLIENT_ID"],
            "Username": email,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            _get_cognito_client().resend_confirmation_code(**kwargs)
        except ClientError as exc:
            raise _map_cognito_error(exc, "Could not resend confirmation code")
        except BotoCoreError as exc:
            raise CognitoClientError(
                502, f"Could not resend confirmation code: {exc}"
            )

    @staticmethod
    def forgot_password(email: str) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.COGNITO["APP_CLIENT_ID"],
            "Username": email,
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            kwargs["SecretHash"] = secret_hash

        try:
            _get_cognito_client().forgot_password(**kwargs)
        except ClientError as exc:
            raise _map_cognito_error(exc, "Could not start password reset")
        except BotoCoreError as exc:
            raise CognitoClientError(
                502, f"Could not start password reset: {exc}"
            )

    @staticmethod
    def confirm_forgot_password(email: str, code: str, new_password: str) -> None:
        kwargs: dict[str, Any] = {
            "ClientId": settings.COGNITO["APP_CLIENT_ID"],
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
            raise _map_cognito_error(exc, "Could not reset password")
        except BotoCoreError as exc:
            raise CognitoClientError(502, f"Could not reset password: {exc}")


cognito_client = CognitoClient()
