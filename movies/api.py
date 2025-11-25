from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Q
from .models import Movie, Genre, Rating, Review
from .schemas import *
from shared_auth.auth import bearer_auth


# ======== Helper ========
def get_current_user(request):
    """
    Отримує автентифікованого користувача (User) з об'єкта запиту.

    В Django Ninja автентифікований об'єкт зберігається в 'request.auth'.

    :param request: Об'єкт HttpRequest.
    :return: Об'єкт моделі User.
    """
    return request.auth


# ======== Movies Router ========
movies_router = Router(tags=["Movies"], auth=bearer_auth)


@movies_router.post("/", response={201: MovieOut})
def create_movie(request, payload: MovieIn):
    """
    Створює новий фільм у каталозі.

    Прив'язує фільм до поточного користувача як 'added_by' (додано_ким).
    Встановлює жанри на основі наданих ID.

    :param request: Об'єкт HttpRequest (з автентифікованим користувачем).
    :param payload: Дані нового фільму (включаючи title, release_date, genre_ids).
    :type payload: MovieIn
    :status 201: Фільм успішно створено.
    :return: Об'єкт створеного фільму.
    :rtype: MovieOut
    """
    user = get_current_user(request)

    movie = Movie.objects.create(
        title=payload.title,
        release_date=payload.release_date,
        description=payload.description,
        added_by=user
    )
    movie.genres.set(payload.genre_ids)
    return 201, movie


@movies_router.get("/", response=List[MovieOut])
def list_movies(
        request,
        genre_id: Optional[int] = Query(None),
        min_rating: Optional[float] = Query(None),
        release_year: Optional[int] = Query(None),
        search: Optional[str] = Query(None)
):
    """
    Повертає список фільмів з підтримкою фільтрації, пошуку та анотування рейтингом.

    Фільтрація:
    * Анотує кожен фільм середнім рейтингом (`avg_rating`).
    * Підтримує фільтрацію за ID жанру, мінімальним рейтингом, роком випуску.
    * Підтримує пошук за назвою (`title__icontains`).
    Результат сортується за спаданням рейтингу, потім за назвою.

    :param request: Об'єкт HttpRequest.
    :param genre_id: ID жанру для фільтрації.
    :type genre_id: Optional[int]
    :param min_rating: Мінімальний середній рейтинг фільму.
    :type min_rating: Optional[float]
    :param release_year: Рік випуску фільму.
    :type release_year: Optional[int]
    :param search: Текстовий пошук за назвою фільму.
    :type search: Optional[str]
    :return: Список об'єктів фільмів.
    :rtype: List[MovieOut]
    """
    queryset = Movie.objects.all().annotate(
        avg_rating=Avg('ratings__value')
    ).prefetch_related('genres')

    if genre_id:
        queryset = queryset.filter(genres__id=genre_id)

    if min_rating is not None:
        queryset = queryset.filter(avg_rating__gte=min_rating)

    if release_year:
        queryset = queryset.filter(release_date__year=release_year)

    if search:
        queryset = queryset.filter(Q(title__icontains=search))

    return queryset.order_by('-avg_rating', 'title')


@movies_router.get("/{movie_id}/", response=MovieOut)
def get_movie(request, movie_id: int):
    """
    Повертає деталі конкретного фільму за його ID.

    :param request: Об'єкт HttpRequest.
    :param movie_id: ID фільму.
    :type movie_id: int
    :raises Http404: Якщо фільм не знайдено.
    :return: Об'єкт фільму.
    :rtype: MovieOut
    """
    return get_object_or_404(Movie, id=movie_id)


@movies_router.put("/{movie_id}/", response=MovieOut)
def update_movie(request, movie_id: int, payload: MovieIn):
    """
    Оновлює існуючий фільм.

    Дозволяє оновлювати фільм лише користувачу, який його додав ('added_by').
    Підтримує часткове оновлення (PATCH-подібна поведінка).
    Оновлює як текстові поля, так і M2M зв'язок (жанри).

    :param request: Об'єкт HttpRequest.
    :param movie_id: ID фільму для оновлення.
    :type movie_id: int
    :param payload: Дані для оновлення фільму.
    :type payload: MovieIn
    :raises Http404: Якщо фільм не знайдено або користувач не є 'added_by'.
    :return: Оновлений об'єкт фільму.
    :rtype: MovieOut
    """
    user = get_current_user(request)
    movie = get_object_or_404(Movie, id=movie_id, added_by=user)

    for attr, value in payload.dict(exclude_unset=True).items():
        if attr == 'genre_ids':
            movie.genres.set(value)
        else:
            setattr(movie, attr, value)

    movie.save()
    return movie


@movies_router.delete("/{movie_id}/", response={204: None})
def delete_movie(request, movie_id: int):
    """
    Видаляє фільм.

    Дозволяє видаляти фільм лише користувачу, який його додав ('added_by').

    :param request: Об'єкт HttpRequest.
    :param movie_id: ID фільму для видалення.
    :type movie_id: int
    :raises Http404: Якщо фільм не знайдено або користувач не є 'added_by'.
    :status 204: Успішне видалення (без вмісту).
    :return: None.
    """
    user = get_current_user(request)
    movie = get_object_or_404(Movie, id=movie_id, added_by=user)
    movie.delete()
    return 204, None


# ======== Genres Router ========
genres_router = Router(tags=["Genres"], auth=bearer_auth)


@genres_router.post("/", response={201: GenreOut})
def create_genre(request, payload: GenreIn):
    """
    Створює новий жанр (наприклад, 'Фантастика', 'Драма').

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового жанру.
    :type payload: GenreIn
    :status 201: Жанр успішно створено.
    :return: Об'єкт створеного жанру.
    :rtype: GenreOut
    """
    genre = Genre.objects.create(**payload.dict())
    return 201, genre


@genres_router.get("/", response=List[GenreOut])
def list_genres(request):
    """
    Повертає список усіх доступних жанрів.

    :param request: Об'єкт HttpRequest.
    :return: Список об'єктів жанрів.
    :rtype: List[GenreOut]
    """
    return Genre.objects.all()


# ======== Ratings Router ========
ratings_router = Router(tags=["Ratings"], auth=bearer_auth)


@ratings_router.post("/{movie_id}/", response=RatingOut)
def add_rating(request, movie_id: int, payload: RatingIn):
    """
    Додає або оновлює рейтинг фільму поточним користувачем.

    Використовує `update_or_create` для забезпечення унікальності:
    кожен користувач може залишити лише один рейтинг для одного фільму.

    :param request: Об'єкт HttpRequest.
    :param movie_id: ID фільму, який оцінюється.
    :type movie_id: int
    :param payload: Об'єкт з числовим значенням рейтингу (value).
    :type payload: RatingIn
    :raises Http404: Якщо фільм не знайдено.
    :return: Об'єкт створеного або оновленого рейтингу.
    :rtype: RatingOut
    """
    user = get_current_user(request)
    movie = get_object_or_404(Movie, id=movie_id)

    rating, created = Rating.objects.update_or_create(
        movie=movie,
        user=user,
        defaults={'value': payload.value}
    )
    return rating


# ======== Reviews Router ========
reviews_router = Router(tags=["Reviews"], auth=bearer_auth)


@reviews_router.post("/{movie_id}/", response={201: ReviewOut})
def add_review(request, movie_id: int, payload: ReviewIn):
    """
    Додає новий текстовий відгук до фільму поточним користувачем.

    На відміну від рейтингу, користувач може залишити кілька відгуків.

    :param request: Об'єкт HttpRequest.
    :param movie_id: ID фільму, до якого додається відгук.
    :type movie_id: int
    :param payload: Об'єкт з текстом відгуку.
    :type payload: ReviewIn
    :raises Http404: Якщо фільм не знайдено.
    :status 201: Відгук успішно створено.
    :return: Об'єкт створеного відгуку.
    :rtype: ReviewOut
    """
    user = get_current_user(request)
    movie = get_object_or_404(Movie, id=movie_id)

    review = Review.objects.create(
        movie=movie,
        user=user,
        text=payload.text
    )
    return 201, review


@reviews_router.get("/{movie_id}/", response=List[ReviewOut])
def list_reviews(request, movie_id: int):
    """
    Повертає список усіх відгуків для конкретного фільму.

    Відгуки сортуються за датою створення у зворотному порядку (найновіші перші).

    :param request: Об'єкт HttpRequest.
    :param movie_id: ID фільму, відгуки до якого потрібно отримати.
    :type movie_id: int
    :raises Http404: Якщо фільм не знайдено.
    :return: Список об'єктів відгуків.
    :rtype: List[ReviewOut]
    """
    movie = get_object_or_404(Movie, id=movie_id)
    return movie.reviews.all().order_by('-created_at')
