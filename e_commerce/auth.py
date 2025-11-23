from django.contrib.auth import get_user_model
from django.http import HttpRequest


class AuthRequest(HttpRequest):
    User = get_user_model()
    auth: User
