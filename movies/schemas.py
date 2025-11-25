from ninja import Schema
from typing import List, Optional
from datetime import date, datetime


# Жанри
class GenreIn(Schema):
    """
    Схема вхідних даних для створення нового жанру.
    """
    name: str
    """Назва жанру (обов'язкове поле)."""


class GenreOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Genre.
    """
    id: int
    """Унікальний ідентифікатор жанру."""

    name: str
    """Назва жанру."""


class ReviewIn(Schema):
    """
    Схема вхідних даних для додавання нового текстового відгуку.
    """
    text: str
    """Текст відгуку (обов'язкове поле)."""


class ReviewOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Review.
    """
    id: int
    """Унікальний ідентифікатор відгуку."""

    user_username: str
    """Ім'я користувача, який залишив відгук (вирішується через метод resolve_user_username)."""

    text: str
    """Текст відгуку."""

    created_at: datetime
    """Дата та час створення відгуку."""

    @staticmethod
    def resolve_user_username(obj):
        """Отримує ім'я користувача з пов'язаного об'єкта User."""
        return obj.user.username


class RatingIn(Schema):
    """
    Схема вхідних даних для додавання або оновлення оцінки.
    """
    value: int
    """Числове значення оцінки (очікується від 1 до 10)."""


class RatingOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Rating.
    """
    user_username: str
    """Ім'я користувача, який залишив оцінку."""

    value: int
    """Числове значення оцінки."""

    @staticmethod
    def resolve_user_username(obj):
        """Отримує ім'я користувача з пов'язаного об'єкта User."""
        return obj.user.username


class MovieIn(Schema):
    """
    Схема вхідних даних для створення або оновлення об'єкта Movie.
    """
    title: str
    """Назва фільму."""

    release_date: date
    """Дата випуску фільму (очікується об'єкт date)."""

    description: Optional[str] = None
    """Опис фільму (необов'язкове поле)."""

    genre_ids: List[int]
    """Список ID жанрів, до яких належить фільм (використовується для M2M зв'язку)."""


class MovieOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Movie.
    """
    id: int
    """Унікальний ідентифікатор фільму."""

    title: str
    """Назва фільму."""

    release_date: date
    """Дата випуску фільму."""

    description: Optional[str] = None
    """Опис фільму."""

    genres: List[GenreOut]
    """Список жанрів фільму (використовує схему GenreOut)."""

    average_rating: float
    """Середній рейтинг фільму (обчислюється через @property в моделі)."""
