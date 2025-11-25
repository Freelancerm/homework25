from ninja import NinjaAPI
from .api import task_router
from shared_auth.api import get_auth_router
from django.urls import path

api_task_manager = NinjaAPI(title="Task Management API", version="1.0.0")

api_task_manager.add_router("/", get_auth_router())
api_task_manager.add_router("/tasks/", task_router)

urlpatterns = [
    path('api/', api_task_manager.urls),
]
