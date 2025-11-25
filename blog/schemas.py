from ninja import Schema
from typing import List
from datetime import datetime


# --- Теги ---
class TagIn(Schema):
    """
    Схема вхідних даних для створення нового тегу.
    """
    name: str
    """Назва тегу (обов'язкове поле)."""


class TagOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Tag.
    """
    id: int
    """Унікальний ідентифікатор тегу."""

    name: str
    """Назва тегу."""


# --- Коментарі ---
class CommentIn(Schema):
    """
    Схема вхідних даних для додавання нового коментаря до посту.
    """
    text: str
    """Текст коментаря (обов'язкове поле)."""


class CommentOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Comment.
    """
    id: int
    """Унікальний ідентифікатор коментаря."""

    author_username: str
    """Ім'я користувача, який залишив коментар (вирішується через метод resolve_author_username)."""

    text: str
    """Текст коментаря."""

    created_at: datetime
    """Дата та час створення коментаря."""

    @staticmethod
    def resolve_author_username(obj):
        """Отримує ім'я користувача з пов'язаного об'єкта User."""
        return obj.author.username


# --- Пости ---
class PostIn(Schema):
    """
    Схема вхідних даних для створення або оновлення об'єкта Post.
    """
    title: str
    """Заголовок посту (обов'язкове поле)."""

    content: str
    """Повний вміст посту (обов'язкове поле)."""

    tag_ids: List[int]
    """Список ID тегів для прив'язки до посту (використовується для M2M зв'язку)."""


class PostOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Post.
    """
    id: int
    """Унікальний ідентифікатор посту."""

    title: str
    """Заголовок посту."""

    content: str
    """Вміст посту."""

    author_username: str
    """Ім'я користувача, який є автором посту (вирішується через метод resolve_author_username)."""

    created_at: datetime
    """Дата та час створення посту."""

    updated_at: datetime
    """Дата та час останнього оновлення посту."""

    tags: List[TagOut]
    """Список тегів, пов'язаних із постом (використовує вкладену схему TagOut)."""

    comments_count: int
    """Кількість коментарів до посту (вирішується через метод resolve_comments_count)."""

    @staticmethod
    def resolve_author_username(obj):
        """Отримує ім'я користувача з пов'язаного об'єкта User."""
        return obj.author.username

    @staticmethod
    def resolve_comments_count(obj):
        """Підраховує кількість коментарів, пов'язаних із постом (використовує QuerySet)."""
        return obj.comments.count()
