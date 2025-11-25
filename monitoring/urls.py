from django.urls import path
from ninja import NinjaAPI
from .api import router as monitoring_router
from shared_auth.api import get_auth_router

api = NinjaAPI(
    title="Server Monitoring API",
    version='1.0.0',
    urls_namespace='monitoring_api_v1'
)

api.add_router("/", get_auth_router())
api.add_router("/monitoring/", monitoring_router)  # Сервери, Метрики, Сповіщення

urlpatterns = [
    path('api/', api.urls),
]
