from django.db import models
from django.contrib.auth.models import User


# --- Теги ---
class Tag(models.Model):
    """
    Модель, що представляє тег для категоризації постів.
    """
    name = models.CharField(max_length=50, unique=True)
    """Назва тегу. Поле є унікальним."""

    def __str__(self):
        """Повертає назву тегу."""
        return self.name


# --- Пости ---
class Post(models.Model):
    """
    Модель, що представляє публікацію (пост) у блозі.
    """
    title = models.CharField(max_length=255)
    """Заголовок посту."""

    content = models.TextField()
    """Повний вміст посту."""

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    """
    Зовнішній ключ на модель User, який є автором посту.
    Видалення користувача призводить до видалення його постів (CASCADE).
    Зворотна назва зв'язку: 'blog_posts'.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    """Дата та час створення посту (встановлюється автоматично лише при створенні)."""

    updated_at = models.DateTimeField(auto_now=True)
    """Дата та час останнього оновлення посту (оновлюється при кожному збереженні)."""

    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)
    """
    Зв'язок "багато-до-багатьох" з моделлю Tag.
    Дозволяє привласнити посту кілька тегів.
    Зворотна назва зв'язку: 'posts'. Поле може бути пустим (blank=True).
    """

    def __str__(self):
        """Повертає заголовок посту."""
        return self.title


# --- Коментарі ---
class Comment(models.Model):
    """
    Модель, що представляє коментар, залишений до певного посту.
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    """Пост, до якого належить коментар."""

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    """Користувач, який залишив коментар."""

    text = models.TextField()
    """Текст коментаря."""

    created_at = models.DateTimeField(auto_now_add=True)
    """Дата та час створення коментаря."""

    def __str__(self):
        """Повертає інформацію про автора та пост, до якого залишено коментар."""
        return f"Зроблено комментар користувачем: {self.author.username} у пості: {self.post.title}"
