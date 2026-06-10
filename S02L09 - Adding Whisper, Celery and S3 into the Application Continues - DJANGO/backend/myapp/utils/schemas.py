from rest_framework import serializers


class HelloResponse(serializers.Serializer):
    message = serializers.CharField()


class MeResponse(serializers.Serializer):
    sub = serializers.CharField()
    username = serializers.CharField(allow_null=True, required=False)
    email = serializers.CharField(allow_null=True, required=False)
    name = serializers.CharField(allow_null=True, required=False)
    given_name = serializers.CharField(allow_null=True, required=False)
    family_name = serializers.CharField(allow_null=True, required=False)
    email_verified = serializers.BooleanField(required=False)
    roles = serializers.ListField(child=serializers.CharField())


class HealthResponse(serializers.Serializer):
    status = serializers.CharField()


class RegisterRequest(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=128)
    first_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=80
    )
    last_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=80
    )


class RegisterResponse(serializers.Serializer):
    ok = serializers.BooleanField()
    message = serializers.CharField()
    confirmed = serializers.BooleanField(allow_null=True, required=False)


class LoginRequest(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=1, max_length=128)


class TokenResponse(serializers.Serializer):
    access_token = serializers.CharField()
    id_token = serializers.CharField(allow_null=True, required=False)
    refresh_token = serializers.CharField(allow_null=True, required=False)
    expires_in = serializers.IntegerField(allow_null=True, required=False)
    refresh_expires_in = serializers.IntegerField(
        allow_null=True, required=False
    )
    token_type = serializers.CharField()


class LogoutRequest(serializers.Serializer):
    refresh_token = serializers.CharField()


class LogoutResponse(serializers.Serializer):
    ok = serializers.BooleanField()


class ConfirmSignupRequest(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=1, max_length=20)


class ConfirmSignupResponse(serializers.Serializer):
    ok = serializers.BooleanField()
    confirmed = serializers.BooleanField()
    message = serializers.CharField()


class ResendCodeRequest(serializers.Serializer):
    email = serializers.EmailField()


class ResendCodeResponse(serializers.Serializer):
    ok = serializers.BooleanField()
    message = serializers.CharField()


class ForgotPasswordRequest(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordResponse(serializers.Serializer):
    ok = serializers.BooleanField()
    message = serializers.CharField()


class ResetPasswordRequest(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=1, max_length=20)
    new_password = serializers.CharField(min_length=6, max_length=128)


class ResetPasswordResponse(serializers.Serializer):
    ok = serializers.BooleanField()
    message = serializers.CharField()


class ProjectSummary(serializers.Serializer):
    id = serializers.CharField()
    original_filename = serializers.CharField()
    language = serializers.CharField(allow_null=True, required=False)
    status = serializers.CharField()
    progress = serializers.IntegerField()
    error = serializers.CharField(allow_null=True, required=False)
    has_srt = serializers.BooleanField()
    created_at = serializers.CharField(allow_null=True, required=False)
    updated_at = serializers.CharField(allow_null=True, required=False)


class ProjectCreateResponse(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()


class PresignedUrlResponse(serializers.Serializer):
    url = serializers.CharField()


class ProjectCreateRequest(serializers.Serializer):
    file = serializers.FileField()
    language = serializers.CharField(required=False, allow_blank=True, allow_null=True)
