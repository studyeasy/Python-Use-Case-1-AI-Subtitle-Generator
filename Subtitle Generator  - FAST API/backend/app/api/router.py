from fastapi import APIRouter

from app.controllers import hello_controller, projects_controller

api_router = APIRouter()
api_router.include_router(hello_controller.router)
api_router.include_router(projects_controller.router)
