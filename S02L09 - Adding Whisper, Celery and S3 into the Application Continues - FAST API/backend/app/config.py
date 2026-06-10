from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Subly Application"
    app_version: str = "1.0.0"
    app_description: str = "Backend API (AWS Cognito-fronted auth)"
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    swagger_ui_js: str = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"
    )
    swagger_ui_css: str = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css"
    )

    aws_region: str = "eu-west-2"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_app_client_secret: str | None = None
    cognito_auth_flow: str = "USER_PASSWORD_AUTH"
    cognito_token_use: str = "access"
    cognito_groups_claim: str = "cognito:groups"
    cognito_auto_confirm_sign_up: bool = False
    cognito_issuer_override: str | None = None
    cognito_jwks_url_override: str | None = None

    # Comma-separated list of allowed CORS origins.
    cors_origins: str = "http://localhost:3000"

    # Whisper / transcription
    # Default to "tiny" (~39 MB) so the image stays small and the first task
    # starts almost immediately. Bump to "base"/"small"/"medium"/"large-v3"
    # via WHISPER_MODEL when you need higher accuracy — remember to rebuild
    # so the new model is baked into the image (see backend/Dockerfile).
    whisper_model: str = "tiny"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    # A project that sits in QUEUED/TRANSCRIBING without any progress update for
    # longer than this is considered stuck (worker crashed, network hang, etc.)
    # and gets auto-flipped to FAILED on the next list/get read.
    transcribe_stale_timeout_seconds: int = 1800

    # S3
    s3_bucket: str = ""
    s3_upload_prefix: str = "uploads/"
    s3_subtitle_prefix: str = "subtitles/"
    s3_presign_ttl_seconds: int = 900

    # Celery / Redis
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Database
    database_url: str = "sqlite:////data/subly.db"

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def cognito_issuer(self) -> str:
        if self.cognito_issuer_override:
            return self.cognito_issuer_override.rstrip("/")
        return (
            f"https://cognito-idp.{self.aws_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )

    @property
    def cognito_jwks_url(self) -> str:
        if self.cognito_jwks_url_override:
            return self.cognito_jwks_url_override
        return f"{self.cognito_issuer}/.well-known/jwks.json"


settings = Settings()
