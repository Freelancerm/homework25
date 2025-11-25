from django.db import models
from django.contrib.auth.models import User


# --- Конфігурація Сервера ---
class Server(models.Model):
    """
    Модель для зберігання конфігурації сервера, який підлягає моніторингу.
    """
    name = models.CharField(max_length=100, unique=True)
    """Унікальна назва сервера."""

    ip_address = models.GenericIPAddressField(unique=True)
    """Унікальна IP-адреса сервера."""

    is_active = models.BooleanField(default=True)
    """
    Активний статус. Визначає, чи повинен сервер моніторитися. 
    За замовчуванням: True.
    """

    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    """
    Користувач, який додав сервер до системи. 
    При видаленні користувача поле встановлюється в NULL (SET_NULL).
    """

    def __str__(self):
        """Повертає назву сервера та його IP-адресу."""
        return f"{self.name} ({self.ip_address})"


# --- Правила Критичних Метрик (Alert Rules) ---
class AlertRule(models.Model):
    """
    Модель для визначення критичних правил (порогів) для метрик сервера.
    """

    METRIC_CHOICES = (
        ('CPU_LOAD', 'CPU Load (%)'),
        ('MEMORY_USAGE', 'Memory Usage (%)'),
        ('DISK_USAGE', 'Disk Usage (%)'),
    )
    """Допустимі назви метрик, які можуть мати правило сповіщення."""

    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='alert_rules')
    """Сервер, до якого застосовується правило."""

    metric_name = models.CharField(max_length=50, choices=METRIC_CHOICES)
    """Назва метрики, за якою відбувається моніторинг."""

    threshold = models.FloatField()  # Критичне значення (наприклад, 90.0)
    """Критичне значення, при перевищенні якого генерується сповіщення."""

    class Meta:
        """
        Обмеження унікальності: гарантує, що для одного сервера
        існує лише одне правило на одну метрику (наприклад, не може бути двох правил для 'CPU_LOAD').
        """
        unique_together = ('server', 'metric_name')

    def __str__(self):
        """Повертає опис правила."""
        return f"{self.server.name}: Alert if {self.metric_name} > {self.threshold}%"


# --- Історичні Метрики ---
class Metric(models.Model):
    """
    Модель для зберігання історичних даних моніторингу (метрик).
    """
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='metrics')
    """Сервер, до якого належать ці метрики."""

    # Зберігаємо останній відомий статус
    status = models.BooleanField(default=True)
    """Статус доступності сервера: True (UP) або False (DOWN)."""

    # Фактичні числові метрики
    cpu_load = models.FloatField(null=True, blank=True)
    """Завантаження ЦП у відсотках."""

    memory_usage = models.FloatField(null=True, blank=True)
    """Використання пам'яті у відсотках."""

    disk_usage = models.FloatField(null=True, blank=True)
    """Використання дискового простору у відсотках."""

    timestamp = models.DateTimeField(auto_now_add=True)
    """Дата та час запису метрики (встановлюється автоматично)."""

    def __str__(self):
        """Повертає назву сервера та час запису метрик."""
        return f"Metrics for {self.server.name} at {self.timestamp.strftime('%H:%M')}"


# --- Журнал Сповіщень ---
class AlertLog(models.Model):
    """
    Модель для зберігання журналу згенерованих сповіщень (інцідентів).
    """
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    """Сервер, який спричинив сповіщення."""

    message = models.TextField()
    """Детальне повідомлення про інцидент."""

    is_resolved = models.BooleanField(default=False)
    """Статус сповіщення: чи було воно вирішене/закрите."""

    created_at = models.DateTimeField(auto_now_add=True)
    """Дата та час створення запису сповіщення."""

    def __str__(self):
        """Повертає тип сповіщення, назву сервера та повідомлення."""
        return f"ALERT: {self.server.name} - {self.message}"
