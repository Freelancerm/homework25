from ninja.security import HttpBearer
from .models import AuthToken
from django.contrib.auth.models import User
from typing import Optional


class BearerTokenAuth(HttpBearer):
    """
    Клас для автентифікації користувача за допомогою Bearer Token
    (як у заголовку Authorization: Bearer <token_key>).
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        try:
            auth_token = AuthToken.objects.select_related('user').get(key=token)
            return auth_token.user

        except AuthToken.DoesNotExist:
            return None


bearer_auth = BearerTokenAuth()
