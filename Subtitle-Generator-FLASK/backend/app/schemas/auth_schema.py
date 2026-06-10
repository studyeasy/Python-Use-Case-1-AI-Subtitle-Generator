from marshmallow import Schema, fields, validate


class RegisterRequest(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True, validate=validate.Length(min=6, max=128)
    )
    first_name = fields.String(
        load_default=None, allow_none=True, validate=validate.Length(max=80)
    )
    last_name = fields.String(
        load_default=None, allow_none=True, validate=validate.Length(max=80)
    )


class RegisterResponse(Schema):
    ok = fields.Boolean()
    message = fields.String()
    confirmed = fields.Boolean(allow_none=True)


class LoginRequest(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True, validate=validate.Length(min=1, max=128)
    )


class TokenResponse(Schema):
    access_token = fields.String(required=True)
    id_token = fields.String(allow_none=True)
    refresh_token = fields.String(allow_none=True)
    expires_in = fields.Integer(allow_none=True)
    refresh_expires_in = fields.Integer(allow_none=True)
    token_type = fields.String()


class LogoutRequest(Schema):
    refresh_token = fields.String(required=True)


class LogoutResponse(Schema):
    ok = fields.Boolean()


class ConfirmSignupRequest(Schema):
    email = fields.Email(required=True)
    code = fields.String(required=True, validate=validate.Length(min=1, max=20))


class ConfirmSignupResponse(Schema):
    ok = fields.Boolean()
    confirmed = fields.Boolean()
    message = fields.String()


class ResendCodeRequest(Schema):
    email = fields.Email(required=True)


class ResendCodeResponse(Schema):
    ok = fields.Boolean()
    message = fields.String()


class ForgotPasswordRequest(Schema):
    email = fields.Email(required=True)


class ForgotPasswordResponse(Schema):
    ok = fields.Boolean()
    message = fields.String()


class ResetPasswordRequest(Schema):
    email = fields.Email(required=True)
    code = fields.String(required=True, validate=validate.Length(min=1, max=20))
    new_password = fields.String(
        required=True, validate=validate.Length(min=6, max=128)
    )


class ResetPasswordResponse(Schema):
    ok = fields.Boolean()
    message = fields.String()


class HealthResponse(Schema):
    status = fields.String()
