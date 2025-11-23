from ninja import Router
from .models import AuthToken
from .schemas import LogIn, TokenOut
from django.contrib.auth import authenticate
from .auth import bearer_auth
from ninja.errors import HttpError


def get_auth_router():
    auth_router = Router()

    @auth_router.post("login/", response=TokenOut)
    def login(request, payload: LogIn):
        """
        Ендпоінт для отримання Bearer Token.

        Автентифікує користувача за наданими 'username' та 'password'.
        У разі успіху створює або отримує існуючий AuthToken і повертає його.

        :param payload: Дані для входу (username, password).
        :type payload: LogIn
        :raises HTTPError 401: Якщо надані недійсні облікові дані.
        :return: Об'єкт, що містить Bearer Token.
        :rtype: TokenOut
        """
        user = authenticate(username=payload.username, password=payload.password)

        if user:
            token, created = AuthToken.objects.get_or_create(user=user)
            return TokenOut(token=str(token.key))
        else:
            raise HttpError(401, "Invalid credentials")

    return auth_router
