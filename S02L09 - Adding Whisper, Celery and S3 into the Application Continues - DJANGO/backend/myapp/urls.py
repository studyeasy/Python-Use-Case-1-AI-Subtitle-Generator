from django.urls import path

from myapp.controllers.projects_controller import project_detail, project_srt, projects_collection
from myapp.controllers.system_controller import hello_world

urlpatterns = [
    path("hello", hello_world, name="hello-world"),
    path("projects", projects_collection, name="projects"),
    path("projects/<str:project_id>", project_detail, name="project-detail"),
    path("projects/<str:project_id>/srt", project_srt, name="project-srt"),
]
