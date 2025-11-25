from ninja import NinjaAPI
from .api import post_router, public_router, tags_router
from shared_auth.api import get_auth_router
from django.urls import path

api_blog = NinjaAPI(
    title='Blog API',
    version='1.0.0',
    urls_namespace='blog_api_v1'
)

api_blog.add_router("/", get_auth_router())
api_blog.add_router("/public/", public_router)
api_blog.add_router("/posts/", post_router)
api_blog.add_router("/tags/", tags_router)


urlpatterns = [
    path('api/', api_blog.urls),
]