from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from app.api.router import api_router
from app.config import settings
from app.controllers import auth_controller, me_controller
from app.db.session import Base, engine
from app.models import project as _project_model  # noqa: F401  (register ORM model)
from app.schemas.auth_schema import HealthResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url=None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/docs", include_in_schema=False)
    def swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=settings.app_name,
            swagger_js_url=settings.swagger_ui_js,
            swagger_css_url=settings.swagger_ui_css,
        )

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    # Versioned API (e.g. /api/v1/hello).
    app.include_router(api_router, prefix=settings.api_prefix)

    # Auth-fronting routes: frontend talks to these instead of Cognito.
    app.include_router(auth_controller.router)

    # Back-compat: legacy /api/me alias (same payload as /auth/me).
    app.include_router(me_controller.router, prefix="/api")

    @app.on_event("startup")
    def _create_tables() -> None:
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()
