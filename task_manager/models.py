from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    """
    Модель, що представляє окреме завдання користувача.

    Містить інформацію про назву, опис, поточний статус та терміни.
    """
    STATUS_CHOICES = (
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    )
    """Можливі варіанти статусу завдання."""

    title = models.CharField(max_length=255)
    """Назва завдання (до 255 символів)."""

    description = models.TextField(blank=True)
    """Детальний опис завдання (необов'язкове поле)."""

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    """
    Поточний статус завдання. Обмежується значеннями з STATUS_CHOICES.
    За замовчуванням: 'TODO'.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    """Дата та час створення завдання. Встановлюється автоматично."""

    due_date = models.DateTimeField(null=True, blank=True)
    """Кінцевий термін виконання завдання (опціональне поле)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    """
    Зовнішній ключ на модель користувача (User).
    Вказує, якому користувачу належить завдання.
    Видалення користувача призводить до видалення всіх його завдань (CASCADE).
    """

    def __str__(self):
        """
        Повертає строкове представлення об'єкта (назву завдання).
        """
        return self.title
