from ninja import Schema
from typing import Optional
from datetime import datetime


# --- Server Schemas ---
class ServerIn(Schema):
    """
    Схема вхідних даних для реєстрації нового сервера.
    """
    name: str
    """Назва сервера (обов'язкове поле)."""

    ip_address: str
    """IP-адреса сервера (обов'язкове поле)."""

    is_active: Optional[bool] = True
    """Статус моніторингу (за замовчуванням True)."""


class ServerOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Server.
    """
    id: int
    """Унікальний ідентифікатор сервера."""

    name: str
    """Назва сервера."""

    ip_address: str
    """IP-адреса сервера."""

    is_active: bool
    """Статус активності моніторингу."""

    added_by_username: str
    """Ім'я користувача, який додав сервер (вирішується через метод resolve_added_by_username)."""

    @staticmethod
    def resolve_added_by_username(obj):
        """Отримує ім'я користувача або 'System', якщо автор відсутній."""
        return obj.added_by.username if obj.added_by else "System"


# --- Metric Schemas (Для отримання даних від агента моніторингу) ---
class MetricIn(Schema):
    """
    Схема вхідних даних для надсилання метрик моніторингу від агента.
    """
    status: bool = True
    """Статус доступності сервера: True (UP) або False (DOWN)."""

    cpu_load: Optional[float] = None
    """Завантаження ЦП у відсотках (опціонально)."""

    memory_usage: Optional[float] = None
    """Використання пам'яті у відсотках (опціонально)."""

    disk_usage: Optional[float] = None
    """Використання дискового простору у відсотках (опціонально)."""


class MetricOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Metric.
    """
    server_id: int
    """ID сервера, до якого належать метрики."""

    status: bool
    """Статус доступності."""

    cpu_load: Optional[float]
    """Завантаження ЦП."""

    memory_usage: Optional[float]
    """Використання пам'яті."""

    disk_usage: Optional[float]
    """Використання дискового простору."""

    timestamp: datetime
    """Дата та час запису метрики."""


# --- Alert Rule Schemas ---
class AlertRuleIn(Schema):
    """
    Схема вхідних даних для створення або оновлення правила сповіщення.
    """
    metric_name: str
    """Назва метрики, для якої встановлюється поріг ('CPU_LOAD', 'MEMORY_USAGE', 'DISK_USAGE')."""

    threshold: float
    """Критичне значення порогу, при перевищенні якого генерується сповіщення."""


class AlertRuleOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта AlertRule.
    """
    id: int
    """Унікальний ідентифікатор правила."""

    server_id: int
    """ID сервера, до якого застосовується правило."""

    metric_name: str
    """Назва метрики."""

    threshold: float
    """Критичне значення порогу."""


# --- Alert Log Schemas ---
class AlertLogOut(Schema):
    """
    Схема вихідних даних для представлення запису AlertLog.
    """
    server_name: str
    """Назва сервера, який спричинив сповіщення (вирішується через метод resolve_server_name)."""

    message: str
    """Детальне повідомлення про інцидент."""

    is_resolved: bool
    """Статус вирішення сповіщення."""

    created_at: datetime
    """Дата та час створення запису сповіщення."""

    @staticmethod
    def resolve_server_name(obj):
        """Отримує назву сервера з пов'язаного об'єкта Server."""
        return obj.server.name
