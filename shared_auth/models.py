from django.db import models
from django.contrib.auth.models import User
import uuid


class AuthToken(models.Model):
    """
    Модель для зберігання Bearer токенів автентифікації.

    Встановлює зв'язок "один-до-одного" між користувачем та його токеном.
    Використовується для автентифікації користувачів в API.
    """
    key = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    """
    Унікальний ідентифікатор токена (ключ). 
    Генерується автоматично як UUID і використовується як первинний ключ.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='task_auth_token')
    """
    Зв'язок "один-до-одного" з моделлю користувача (User).
    Видалення користувача призводить до видалення токена.
    Зворотна назва зв'язку: 'auth_token'.
    """

    created = models.DateTimeField(auto_now_add=True)
    """ Дата та час створення токена. """

    def __str__(self):
        """
        Повертає строкове представлення об'єкта (UUID токена).
        """
        return str(self.key)
