from django.urls import path
from ninja import NinjaAPI
from .api import product_router, cart_router, order_router
from shared_auth.api import get_auth_router


api_ecommerce = NinjaAPI(
    title="E-commerce API",
    version='1.0.0',
    urls_namespace='ecommerce_api_v1'
)


api_ecommerce.add_router("/auth/", get_auth_router())
api_ecommerce.add_router("/products/", product_router)
api_ecommerce.add_router("/cart/", cart_router)
api_ecommerce.add_router("/orders/", order_router)

urlpatterns = [
    path('api/', api_ecommerce.urls),
]
