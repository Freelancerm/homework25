from ninja import NinjaAPI
from .api import movies_router, genres_router, ratings_router, reviews_router
from shared_auth.api import get_auth_router
from django.urls import path

api_movies = NinjaAPI(
    title="Movies API",
    version="1.0.0",
    urls_namespace='movies_api_v1'
)

api_movies.add_router("/auth/", get_auth_router())
api_movies.add_router("/movies/", movies_router)
api_movies.add_router("/genres/", genres_router)
api_movies.add_router("/ratings/", ratings_router)
api_movies.add_router("/reviews/", reviews_router)

urlpatterns = [
    path('api/', api_movies.urls),
]
