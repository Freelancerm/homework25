from django.db import models
from django.contrib.auth.models import User


# --- Жанри ---
class Genre(models.Model):
    """
    Модель, що представляє жанр книги (наприклад, Фантастика, Драма).
    """
    name = models.CharField(max_length=100, unique=True)
    """Назва жанру. Поле є унікальним для запобігання дублюванню."""

    def __str__(self):
        """Повертає назву жанру."""
        return self.name


# --- Книги ---
class Book(models.Model):
    """
    Модель, що представляє книгу в каталозі бібліотеки.
    """
    title = models.CharField(max_length=255)
    """Назва книги."""

    author = models.CharField(max_length=255)
    """Автор книги."""

    publication_year = models.IntegerField(null=True, blank=True)
    """Рік видання (може бути пустим)."""

    isbn = models.CharField(max_length=17, unique=True)
    """Унікальний міжнародний стандартний номер книги (ISBN)."""

    genres = models.ManyToManyField(Genre, related_name='books', blank=True)
    """
    Зв'язок "багато-до-багатьох" з моделлю Genre. 
    Книга може мати багато жанрів.
    Зворотна назва зв'язку: 'books'.
    """

    total_copies = models.IntegerField(default=1)
    """Загальна кількість фізичних екземплярів книги, які має бібліотека."""

    @property
    def available_copies(self):
        """
        Обчислює кількість доступних для оренди копій книги.

        Розраховується як: `total_copies` мінус кількість активних (неповернутих) оренд.

        :return: Кількість доступних копій.
        :rtype: int
        """
        rented_count = self.rentals.filter(return_date__isnull=True).count()
        return self.total_copies - rented_count

    def __str__(self):
        """Повертає назву та автора книги."""
        return f"{self.title} by {self.author}"


# --- Оренда (Запозичення) ---
class Rental(models.Model):
    """
    Модель, що фіксує факт оренди книги користувачем.
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='rentals')
    """Книга, яка була орендована."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    """Користувач, який орендував книгу."""

    rental_date = models.DateTimeField(auto_now_add=True)
    """Дата та час початку оренди (автоматично)."""

    return_date = models.DateTimeField(null=True, blank=True)
    """
    Дата та час повернення книги. 
    Якщо NULL, книга вважається орендованою (активною).
    """

    def __str__(self):
        """Повертає інформацію про оренду (користувач та книга)."""
        return f"{self.user.username} орендував {self.book.title}"
