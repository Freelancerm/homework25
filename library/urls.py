# project_name/urls.py (Ваш головний файл)

from django.urls import path
from ninja import NinjaAPI
from library.api import router as library_router
from shared_auth.api import get_auth_router

api = NinjaAPI(
    title="Books Library API",
    version='1.0.0',
    urls_namespace='library_api_v1'
)

api.add_router("/", get_auth_router())
api.add_router("/library/", library_router)

urlpatterns = [
    # ... admin path
    path('api/', api.urls),
]
