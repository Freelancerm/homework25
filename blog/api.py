from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Count
from typing import Optional
from django.http import HttpRequest

from .models import Post, Tag, Comment
from .schemas import *
from shared_auth.auth import bearer_auth

# Застосовуємо авторизацію до роутера постів, де потрібен захист
post_router = Router(tags=["Posts"], auth=bearer_auth)

# Роутер для публічних операцій (наприклад, перегляд тегів)
public_router = Router(tags=["Public"])

# Роутер для приватних операцій керування ресурсами Tags
tags_router = Router(tags=["Tags"], auth=bearer_auth)


def get_current_user(request):
    """
    Отримує автентифікованого користувача (User) з об'єкта запиту.

    В Django Ninja автентифікований об'єкт зберігається в 'request.auth'
    після успішної перевірки Bearer Token.

    :param request: Об'єкт HttpRequest.
    :return: Об'єкт моделі User.
    """
    return request.auth


# --- CRUD для ПОСТІВ (Захищено) ---

@post_router.post("/", response={201: PostOut})
def create_post(request: HttpRequest, payload: PostIn):
    """
    Створення нового посту.

    Автоматично призначає поточного автентифікованого користувача
    автором посту та встановлює надані теги.

    :param request: Об'єкт HttpRequest (з автентифікованим користувачем).
    :param payload: Дані нового посту (title, content, tag_ids).
    :type payload: PostIn
    :status 201: Пост успішно створено.
    :return: Об'єкт створеного посту.
    :rtype: PostOut
    """
    user = get_current_user(request)

    post = Post.objects.create(
        title=payload.title,
        content=payload.content,
        author=user
    )
    # Встановлення тегів
    post.tags.set(payload.tag_ids)
    return 201, post


@post_router.put("/{post_id}/", response=PostOut)
def update_post(request: HttpRequest, post_id: int, payload: PostIn):
    """
    Оновлення існуючого посту.

    Доступно лише користувачу, який є автором посту.
    Підтримує часткове оновлення полів та M2M зв'язку (тегів).

    :param request: Об'єкт HttpRequest.
    :param post_id: ID посту для оновлення.
    :type post_id: int
    :param payload: Дані для оновлення.
    :type payload: PostIn
    :raises Http404: Якщо пост не знайдено або користувач не є автором.
    :return: Оновлений об'єкт посту.
    :rtype: PostOut
    """
    user = get_current_user(request)
    # Шукаємо пост і перевіряємо, чи є користувач автором
    post = get_object_or_404(Post, id=post_id, author=user)

    # Оновлення полів
    for attr, value in payload.dict(exclude_unset=True).items():
        if attr == 'tag_ids':
            post.tags.set(value)
        else:
            setattr(post, attr, value)

    post.save()
    return post


@post_router.delete("/{post_id}/", response={204: None})
def delete_post(request: HttpRequest, post_id: int):
    """
    Видалення посту.

    Доступно лише користувачу, який є автором посту.

    :param request: Об'єкт HttpRequest.
    :param post_id: ID посту для видалення.
    :type post_id: int
    :raises Http404: Якщо пост не знайдено або користувач не є автором.
    :status 204: Успішне видалення (без вмісту).
    :return: None.

    """
    user = get_current_user(request)
    post = get_object_or_404(Post, id=post_id, author=user)
    post.delete()
    return 204, None


# --- ПУБЛІЧНЕ ЧИТАННЯ ПОСТІВ та ФІЛЬТРАЦІЯ ---

@public_router.get("/posts/", response=List[PostOut])
def list_posts(
        request: HttpRequest,
        tag_id: Optional[int] = Query(None, description="Фільтр за ID тегу")
):
    """
    Отримання списку всіх постів.

    Включає оптимізацію:
    * Анотує кожен пост кількістю коментарів (`comments_count`).
    * Використовує `prefetch_related` для оптимізації отримання тегів.
    * Підтримує фільтрацію за ID тегу.
    Пости сортуються за датою створення у зворотному порядку (новіші перші).

    :param request: Об'єкт HttpRequest.
    :param tag_id: ID тегу для фільтрації.
    :type tag_id: Optional[int]
    :return: Список об'єктів постів.
    :rtype: List[PostOut]
    """
    # Оптимізація: підрахунок коментарів у запиті та отримання тегів
    queryset = Post.objects.all().annotate(
        comments_count=Count('comments')
    ).prefetch_related('tags').order_by('-created_at')

    # Фільтрація за тегом
    if tag_id:
        queryset = queryset.filter(tags__id=tag_id)

    return queryset


@public_router.get("/posts/{post_id}/", response=PostOut)
def get_post(request: HttpRequest, post_id: int):
    """
    Отримання деталей одного посту.

    Використовує анотацію для включення кількості коментарів до вихідних даних.

    :param request: Об'єкт HttpRequest.
    :param post_id: ID посту.
    :type post_id: int
    :raises Http404: Якщо пост не знайдено.
    :return: Об'єкт посту з деталями.
    :rtype: PostOut
    """
    # Використовуємо .annotate() для відображення кількості коментарів
    post = get_object_or_404(
        Post.objects.annotate(comments_count=Count('comments')),
        id=post_id
    )
    return post


# --- УПРАВЛІННЯ ТЕГАМИ (Публічне Читання, Приватне Створення) ---

@public_router.get("/tags/", response=List[TagOut])
def list_tags(request: HttpRequest):
    """
    Отримання списку всіх доступних тегів.

    :param request: Об'єкт HttpRequest.
    :return: Список об'єктів тегів.
    :rtype: List[TagOut]
    """
    return Tag.objects.all()


@tags_router.post("/tags/", response={201: TagOut})
def create_tag(request: HttpRequest, payload: TagIn):
    """
    Створення нового тегу.

    Доступно лише автентифікованим користувачам. Використовує `get_or_create`
    для уникнення дублікатів (за умови унікальності поля `name` у моделі).

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового тегу (name).
    :type payload: TagIn
    :status 201: Тег успішно створено (або отримано, якщо існує).
    :return: Об'єкт тегу.
    :rtype: TagOut
    """
    # Додамо перевірку, щоб уникнути дублікатів, хоча це робиться унікальністю в моделі
    tag, created = Tag.objects.get_or_create(name=payload.name)
    return 201, tag


# --- КОМЕНТАРІ (Приватне Додавання, Публічне Читання) ---

@post_router.post("/{post_id}/comments/", response={201: CommentOut})
def add_comment(request: HttpRequest, post_id: int, payload: CommentIn):
    """
    Додавання коментаря до посту.

    Доступно лише автентифікованим користувачам. Користувач автоматично
    призначається автором коментаря.

    :param request: Об'єкт HttpRequest.
    :param post_id: ID посту, до якого додається коментар.
    :type post_id: int
    :param payload: Дані коментаря (text).
    :type payload: CommentIn
    :raises Http404: Якщо пост не знайдено.
    :status 201: Коментар успішно створено.
    :return: Об'єкт створеного коментаря.
    :rtype: CommentOut
    """
    user = get_current_user(request)
    post = get_object_or_404(Post, id=post_id)

    comment = Comment.objects.create(
        post=post,
        author=user,
        text=payload.text
    )
    return 201, comment


@public_router.get("/posts/{post_id}/comments/", response=List[CommentOut])
def list_comments(request: HttpRequest, post_id: int):
    """Отримання всіх коментарів до певного посту."""
    post = get_object_or_404(Post, id=post_id)
    return post.comments.all().order_by('created_at')
