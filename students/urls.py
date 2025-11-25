from django.urls import path
from ninja import NinjaAPI
from .api import admin_router, enrollment_router, grading_router
from shared_auth.api import get_auth_router

api = NinjaAPI(
    title="Student Course Management API",
    version='1.0.0',
    urls_namespace='students_api_v1'
)

api.add_router("/", get_auth_router())  # Ендпоінт для логіну

# 1. Адміністрування: CRUD для студентів/курсів
api.add_router("/admin/", admin_router)

# 2. Реєстрація: Запис на курси
api.add_router("/enrollment/", enrollment_router)

# 3. Оцінювання: Додавання оцінок та метрики
api.add_router("/grading/", grading_router)

urlpatterns = [
    # ... admin path
    path('api/', api.urls),
]
