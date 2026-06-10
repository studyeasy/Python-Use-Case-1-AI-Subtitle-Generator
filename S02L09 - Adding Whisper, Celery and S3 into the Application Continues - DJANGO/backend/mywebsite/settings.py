import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-change-me-for-production"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "myapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mywebsite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mywebsite.wsgi.application"

_SQLITE_PATH = os.environ.get("SQLITE_PATH", "").strip()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(_SQLITE_PATH) if _SQLITE_PATH else BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = False

# CORS — comma-separated allowlist for the Next.js dev server.
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

# AWS Cognito — backend brokers all Cognito calls; the frontend never talks
# to Cognito directly. All values come from the environment.
COGNITO = {
    "REGION": os.environ.get("AWS_REGION", "eu-west-2"),
    "USER_POOL_ID": os.environ.get("COGNITO_USER_POOL_ID", ""),
    "APP_CLIENT_ID": os.environ.get("COGNITO_APP_CLIENT_ID", ""),
    "APP_CLIENT_SECRET": os.environ.get("COGNITO_APP_CLIENT_SECRET", ""),
    "AUTH_FLOW": os.environ.get("COGNITO_AUTH_FLOW", "USER_PASSWORD_AUTH"),
    "TOKEN_USE": os.environ.get("COGNITO_TOKEN_USE", "access"),
    "GROUPS_CLAIM": os.environ.get("COGNITO_GROUPS_CLAIM", "cognito:groups"),
    "AUTO_CONFIRM_SIGN_UP": os.environ.get(
        "COGNITO_AUTO_CONFIRM_SIGN_UP", "false"
    ).lower()
    == "true",
    "ISSUER_OVERRIDE": os.environ.get("COGNITO_ISSUER_OVERRIDE") or None,
    "JWKS_URL_OVERRIDE": os.environ.get("COGNITO_JWKS_URL_OVERRIDE") or None,
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "myapp.services.cognito_service.CognitoAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Subly Application",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Backend API (AWS Cognito-fronted auth)",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "//cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14",
    "SWAGGER_UI_FAVICON_HREF": (
        "//cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/favicon-32x32.png"
    ),
}

# ---------- Whisper / transcription ----------
# Default 'tiny' (~39 MB) — fastest cold-start. Bump to base/small/medium/
# large-v3 via WHISPER_MODEL for higher accuracy. Remember to rebuild so the
# new model is baked into the image (see backend/Dockerfile).
WHISPER = {
    "MODEL": os.environ.get("WHISPER_MODEL", "tiny"),
    "DEVICE": os.environ.get("WHISPER_DEVICE", "cpu"),
    "COMPUTE_TYPE": os.environ.get("WHISPER_COMPUTE_TYPE", "int8"),
}

# A project that sits in QUEUED/TRANSCRIBING without any progress update for
# longer than this is considered stuck and gets auto-flipped to FAILED on the
# next list/get read.
TRANSCRIBE_STALE_TIMEOUT_SECONDS = int(
    os.environ.get("TRANSCRIBE_STALE_TIMEOUT_SECONDS", "1800")
)

# ---------- S3 (subtitle + source media storage) ----------
S3 = {
    "BUCKET": os.environ.get("S3_BUCKET", ""),
    "UPLOAD_PREFIX": os.environ.get("S3_UPLOAD_PREFIX", "uploads/"),
    "SUBTITLE_PREFIX": os.environ.get("S3_SUBTITLE_PREFIX", "subtitles/"),
    "PRESIGN_TTL_SECONDS": int(os.environ.get("S3_PRESIGN_TTL_SECONDS", "900")),
}

# ---------- Celery / Redis ----------
CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL", "redis://redis:6379/0"
)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://redis:6379/1"
)
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TRACK_STARTED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
