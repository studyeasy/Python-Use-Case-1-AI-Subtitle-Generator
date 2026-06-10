from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from myapp.controllers.auth_controller import (
    confirm,
    forgot_password,
    login,
    logout,
    me,
    register,
    resend_confirmation,
    reset_password,
)
from myapp.controllers.system_controller import health

urlpatterns = [
    path("", RedirectView.as_view(url="/docs", permanent=False)),
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    # Versioned API (e.g. /api/v1/hello).
    path("api/v1/", include("myapp.urls")),
    # Auth endpoints — what the frontend calls.
    path("auth/register", register, name="auth-register"),
    path("auth/confirm", confirm, name="auth-confirm"),
    path(
        "auth/resend-confirmation",
        resend_confirmation,
        name="auth-resend-confirmation",
    ),
    path("auth/forgot-password", forgot_password, name="auth-forgot-password"),
    path("auth/reset-password", reset_password, name="auth-reset-password"),
    path("auth/login", login, name="auth-login"),
    path("auth/logout", logout, name="auth-logout"),
    path("auth/me", me, name="auth-me"),
    # Legacy alias kept for back-compat.
    path("api/me", me, name="me"),
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
