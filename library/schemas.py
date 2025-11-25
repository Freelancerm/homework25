from ninja import Schema
from typing import List, Optional
from datetime import datetime


# --- Жанри ---
class GenreOut(Schema):
    id: int
    name: str


# --- Книги ---
class BookIn(Schema):
    title: str
    author: str
    isbn: str
    publication_year: Optional[int] = None
    total_copies: int = 1
    genre_ids: Optional[List[int]] = []  # ID жанрів


class BookOut(Schema):
    id: int
    title: str
    author: str
    isbn: str
    publication_year: Optional[int]
    total_copies: int
    available_copies: int  # @property з моделі
    genres: List[GenreOut]  # Вкладена схема


# --- Оренда ---
class RentalOut(Schema):
    id: int
    book_title: str
    user_username: str
    rental_date: datetime
    return_date: Optional[datetime]

    @staticmethod
    def resolve_book_title(obj):
        return obj.book.title

    @staticmethod
    def resolve_user_username(obj):
        return obj.user.username
