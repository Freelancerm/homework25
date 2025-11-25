from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# Жанри
class Genre(models.Model):
    """
    Модель, що представляє жанр фільму (наприклад, Драма, Комедія).
    """
    name = models.CharField(max_length=100, unique=True)
    """Назва жанру. Поле є унікальним для запобігання дублюванню."""

    def __str__(self):
        """Повертає назву жанру."""
        return self.name


# Фільми
class Movie(models.Model):
    """
    Модель, що представляє фільм у каталозі.
    """
    title = models.CharField(max_length=255)
    """Назва фільму."""

    release_date = models.DateField()
    """Дата випуску фільму."""

    description = models.TextField(blank=True)
    """Опис фільму (необов'язкове поле)."""

    genres = models.ManyToManyField(Genre, related_name='movies')
    """
    Зв'язок "багато-до-багатьох" з моделлю Genre. 
    Фільм може мати багато жанрів, і жанр може мати багато фільмів.
    Зворотна назва зв'язку: 'movies'.
    """

    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_movies')
    """
    Зовнішній ключ на модель User, який додав фільм. 
    Якщо користувач видаляється, поле встановлюється в NULL (SET_NULL).
    Зворотна назва зв'язку: 'added_movies'.
    """

    @property
    def average_rating(self):
        """
        Обчислює середній рейтинг фільму на основі усіх пов'язаних об'єктів Rating.

        :return: Середній рейтинг (float), або 0.0, якщо рейтинги відсутні.
        :rtype: float
        """
        return self.ratings.aggregate(models.Avg('value'))['value__avg'] or 0.0

    def __str__(self):
        """Повертає назву фільму."""
        return self.title


# Рейтинги
class Rating(models.Model):
    """
    Модель, що представляє оцінку фільму, залишену користувачем.
    """
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    """Фільм, який оцінюється."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    """Користувач, який залишив оцінку."""

    value = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    """
    Числове значення оцінки (від 1 до 10).
    Використовуються валідатори для обмеження діапазону.
    """

    class Meta:
        """
        Обмеження унікальності: гарантує, що кожен користувач
        може залишити лише один рейтинг для кожного фільму.
        """
        unique_together = ('movie', 'user')

    def __str__(self):
        """Повертає назву фільму, оцінку та ім'я користувача."""
        return f"{self.movie.title}: {self.value}/10 залишено користувачем: {self.user.username}"


# Відгуки
class Review(models.Model):
    """
    Модель, що представляє текстовий відгук користувача про фільм.
    """
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    """Фільм, до якого відноситься відгук."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    """Користувач, який залишив відгук."""

    text = models.TextField()
    """Повний текст відгуку."""

    created_at = models.DateTimeField(auto_now_add=True)
    """Дата та час створення відгуку."""

    def __str__(self):
        """Повертає фільм та користувача, пов'язаних із відгуком."""
        return f"Відгук для фільму: {self.movie.title} від користувача: {self.user.username}"
