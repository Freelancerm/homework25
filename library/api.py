from ninja import Router, Query
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from .models import Book, Genre, Rental
from .schemas import *
from shared_auth.auth import bearer_auth

# Роутер, який вимагає автентифікації для CRUD книг та оренди
router = Router(tags=["Library Management"], auth=bearer_auth)


def get_current_user(request):
    """
    Отримує автентифікованого користувача (User) з об'єкта запиту.

    В Django Ninja автентифікований об'єкт зберігається в 'request.auth'
    після успішної перевірки Bearer Token.

    :param request: Об'єкт HttpRequest.
    :return: Об'єкт моделі User.
    """
    return request.auth


# ==========================================================
#                         CRUD КНИГ
# ==========================================================

# --- 1. Створення Книги ---
@router.post("/books/", response={201: BookOut})
def create_book(request, payload: BookIn):
    """
    Створює новий запис книги в каталозі бібліотеки.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нової книги (title, author, isbn, total_copies, genre_ids).
    :type payload: BookIn
    :status 201: Книга успішно створена.
    :return: Об'єкт створеної книги.
    :rtype: BookOut
    """
    book = Book.objects.create(
        title=payload.title,
        author=payload.author,
        isbn=payload.isbn,
        publication_year=payload.publication_year,
        total_copies=payload.total_copies
    )
    if payload.genre_ids:
        book.genres.set(payload.genre_ids)

    return 201, book


# --- 2. Пошук та Список Книг ---
@router.get("/books/", response=List[BookOut])
def search_books(
        request,
        query: Optional[str] = Query(None, description="Пошук за назвою, автором або ISBN"),
        genre_id: Optional[int] = Query(None, description="Фільтр за ID жанру")
):
    """
    Повертає список книг з можливістю пошуку та фільтрації.

    Пошук виконується за полями 'title', 'author' та 'isbn' одночасно (логіка OR).
    Також підтримується фільтрація за ID жанру.

    :param request: Об'єкт HttpRequest.
    :param query: Текстовий запит для пошуку.
    :type query: Optional[str]
    :param genre_id: ID жанру для фільтрації.
    :type genre_id: Optional[int]
    :return: Список об'єктів книг.
    :rtype: List[BookOut]
    """
    queryset = Book.objects.all().prefetch_related('genres')

    # Пошук
    if query:
        # Q об'єкт дозволяє OR-запити
        queryset = queryset.filter(
            models.Q(title__icontains=query) |
            models.Q(author__icontains=query) |
            models.Q(isbn__icontains=query)
        )

    # Фільтрація за жанром
    if genre_id:
        queryset = queryset.filter(genres__id=genre_id)

    return queryset.order_by('title')


# --- 3. Отримання однієї Книги ---
@router.get("/books/{book_id}/", response=BookOut)
def get_book(request, book_id: int):
    """
    Повертає деталі конкретної книги за її ID.

    :param request: Об'єкт HttpRequest.
    :param book_id: ID книги.
    :type book_id: int
    :raises Http404: Якщо книга не знайдена.
    :return: Об'єкт книги.
    :rtype: BookOut
    """
    book = get_object_or_404(Book, id=book_id)
    return book


# --- 4. Видалення Книги ---
@router.delete("/books/{book_id}/", response={204: None})
def delete_book(request, book_id: int):
    """
    Видаляє книгу з каталогу.

    :param request: Об'єкт HttpRequest.
    :param book_id: ID книги для видалення.
    :type book_id: int
    :raises Http404: Якщо книга не знайдена.
    :status 204: Успішне видалення (без вмісту).
    :return: None.
    """
    # Доступно лише авторизованим
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    return 204, None


# ==========================================================
#                         ОРЕНДА КНИГ
# ==========================================================

# --- 1. Взяти Книгу (Орендувати) ---
@router.post("/books/{book_id}/rent/", response={201: RentalOut})
@transaction.atomic  # Забезпечення цілісності: перевірка наявності та створення оренди
def rent_book(request, book_id: int):
    """
    Створює запис оренди книги для поточного користувача.

    Операція атомарна. Включає перевірки:
    1. Чи не орендована книга користувачем вже.
    2. Чи є доступні копії книги (`book.available_copies > 0`).

    :param request: Об'єкт HttpRequest.
    :param book_id: ID книги для оренди.
    :type book_id: int
    :raises HttpError 404: Якщо книга вже орендована цим користувачем.
    :raises HttpError 400: Якщо немає доступних копій.
    :status 201: Оренда успішно створена.
    :return: Об'єкт створеної оренди.
    :rtype: RentalOut
    """
    user = get_current_user(request)
    book = get_object_or_404(Book, id=book_id)

    # Перевірка, чи не має користувач уже цю книгу
    if book.rentals.filter(user=user, return_date__isnull=True).exists():
        raise (404, "Ця книга уже арендована вами!")

    # Перевірка наявності доступних копій
    if book.available_copies <= 0:
        raise HttpError(400, "Всі копії цієї книги арендовано")

    rental = Rental.objects.create(book=book, user=user)
    return 201, rental


# --- 2. Повернути Книгу ---
@router.post("/rentals/{rental_id}/return/", response=RentalOut)
def return_book(request, rental_id: int):
    """
    Закриває активний запис оренди, встановлюючи `return_date` на поточний час.

    Доступно лише користувачу, який створив цю оренду.

    :param request: Об'єкт HttpRequest.
    :param rental_id: ID запису оренди, який потрібно закрити.
    :type rental_id: int
    :raises Http404: Якщо активна оренда з цим ID та користувачем не знайдена.
    :return: Оновлений об'єкт оренди.
    :rtype: RentalOut
    """
    user = get_current_user(request)
    # Знаходимо активну оренду, створену цим користувачем
    rental = get_object_or_404(
        Rental,
        id=rental_id,
        user=user,
        return_date__isnull=True  # Книга ще не повернута
    )

    rental.return_date = datetime.now()
    rental.save()

    return rental


# --- 3. Історія Оренди Користувача ---
@router.get("/my-rentals/", response=List[RentalOut])
def list_my_rentals(request):
    """
    Повертає повну історію оренди книг для поточного користувача.

    :param request: Об'єкт HttpRequest.
    :return: Список об'єктів оренди, відсортований за спаданням дати оренди.
    :rtype: List[RentalOut]
    """
    user = get_current_user(request)
    return Rental.objects.filter(user=user).select_related('book').order_by('-rental_date')


# ==========================================================
#                        ЖАНРИ
# ==========================================================

@router.post("/genres/", response={201: GenreOut})
def create_genre(request, payload: GenreOut):
    """
    Створює новий жанр у системі.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового жанру (name).
    :type payload: GenreOut
    :status 201: Жанр успішно створено.
    :return: Об'єкт створеного жанру.
    :rtype: GenreOut
    """
    # Додавання жанрів доступне авторизованим користувачам
    genre = Genre.objects.create(name=payload.name)
    return 201, genre


@router.get("/genres/", response=List[GenreOut])
def list_genres(request):
    """
    Повертає список усіх доступних жанрів.

    :param request: Об'єкт HttpRequest.
    :return: Список об'єктів жанрів.
    :rtype: List[GenreOut]
    """
    return Genre.objects.all()
