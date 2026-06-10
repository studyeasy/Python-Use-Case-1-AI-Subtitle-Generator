from flask import Flask, redirect
from flask_cors import CORS
from flask_smorest import Api

from app.config import settings
from app.controllers import (
    auth_controller,
    hello_controller,
    me_controller,
    projects_controller,
)
from app.db.session import Base, engine
from app.models import project as _project_model  # noqa: F401  (register ORM model)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["API_TITLE"] = settings.app_name
    app.config["API_VERSION"] = settings.app_version
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = settings.swagger_ui_url
    app.config["API_SPEC_OPTIONS"] = {
        "info": {
            "title": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
    }

    CORS(
        app,
        resources={r"/*": {"origins": settings.cors_origin_list}},
        supports_credentials=True,
    )

    api = Api(app)
    api.register_blueprint(
        hello_controller.blp,
        url_prefix=f"{settings.api_prefix}/hello",
    )
    api.register_blueprint(
        projects_controller.blp,
        url_prefix=f"{settings.api_prefix}/projects",
    )
    # Auth-fronting routes the frontend calls.
    api.register_blueprint(auth_controller.blp, url_prefix="/auth")
    # Legacy alias: /api/me (same payload as /auth/me).
    api.register_blueprint(me_controller.blp, url_prefix="/api/me")

    Base.metadata.create_all(bind=engine)

    @app.route("/")
    def index():
        return redirect("/docs")

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
