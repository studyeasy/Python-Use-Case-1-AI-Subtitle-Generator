from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    first_name: str | None = Field(default=None, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)


class RegisterResponse(BaseModel):
    ok: bool = True
    message: str = "User registered"
    confirmed: bool | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    id_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    refresh_expires_in: int | None = None
    token_type: str = "Bearer"


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class LogoutResponse(BaseModel):
    ok: bool = True


class ConfirmSignupRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=1, max_length=20)


class ConfirmSignupResponse(BaseModel):
    ok: bool = True
    confirmed: bool = True
    message: str = "User confirmed"


class ResendCodeRequest(BaseModel):
    email: EmailStr


class ResendCodeResponse(BaseModel):
    ok: bool = True
    message: str = "Confirmation code sent"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    ok: bool = True
    message: str = "Password reset code sent"


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=1, max_length=20)
    new_password: str = Field(min_length=6, max_length=128)


class ResetPasswordResponse(BaseModel):
    ok: bool = True
    message: str = "Password reset"


class HealthResponse(BaseModel):
    status: str = "ok"
