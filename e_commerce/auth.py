from django.contrib.auth import get_user_model
from django.http import HttpRequest


class AuthRequest(HttpRequest):
    """
    Клас-схема для покращення типізації об'єкта HttpRequest в API.

    Цей клас успадковується від стандартного HttpRequest і додає
    атрибут 'auth', який гарантовано містить автентифікованого користувача.
    Він використовується в сигнатурах функцій (views/ендпоінтів)
    для забезпечення статичної перевірки типів.
    """
    User = get_user_model()
    auth: User
