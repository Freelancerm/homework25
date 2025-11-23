from ninja import Router
from .models import Task
from .schemas import TaskIn, TaskOut
from shared_auth.auth import bearer_auth
from django.shortcuts import get_object_or_404
from typing import List, Optional


# Роутер для завдань (Task CRUD)
task_router = Router(auth=bearer_auth)


def get_current_user(request):
    """
    Отримує автентифікованого користувача з об'єкта запиту.

    В Django Ninja аутентифікований об'єкт (у цьому випадку об'єкт User)
    зберігається в атрибуті 'request.auth' після успішної перевірки токена.

    :param request: Об'єкт HttpRequest.
    :return: Об'єкт моделі User.
    """
    return request.auth


# СТВОРЕННЯ (Create)
@task_router.post("/", response={201: TaskOut})
def create_task(request, payload: TaskIn):
    """
    Створює нове завдання для поточного автентифікованого користувача.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового завдання (наприклад, title, description, due_date).
    :type payload: TaskIn
    :status 201: Завдання успішно створено.
    :return: Об'єкт створеного завдання.
    :rtype: TaskOut
    """
    user = get_current_user(request)
    task = Task.objects.create(**payload.dict(), user=user)
    return 201, task


# ЧИТАННЯ (Read) - Отримання списку + фільтрація/сортування
@task_router.get("/", response=List[TaskOut])
def list_tasks(
        request,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
):
    """
    Повертає список завдань поточного автентифікованого користувача.

    Підтримує опціональну фільтрацію за статусом та сортування за полем.

    :param request: Об'єкт HttpRequest.
    :param status: Опціональний статус для фільтрації (наприклад, 'TODO', 'DONE').
    :type status: Optional[str]
    :param sort_by: Опціональне поле для сортування (наприклад, 'created_at', '-due_date').
                    Підтримуються: 'created_at', 'due_date', '-created_at', '-due_date'.
    :type sort_by: Optional[str]
    :return: Список об'єктів завдань.
    :rtype: List[TaskOut]
    """
    user = get_current_user(request)
    # Фільтруємо завдання, щоб показати тільки завдання поточного користувача
    queryset = Task.objects.filter(user=user)

    # Фільтрація за статусом
    if status:
        queryset = queryset.filter(status=status.upper())

    # Сортування
    valid_sorts = ['created_at', 'due_date' '-created_at', '-due_date']
    if sort_by in valid_sorts:
        queryset = queryset.order_by(sort_by)

    return queryset


# ЧИТАННЯ (Read) - Отримання одного завдання
@task_router.get("/{task_id}/", response=TaskOut)
def get_task(request, task_id: int):
    """
    Повертає деталі конкретного завдання за його ID.

    Перевіряє, чи належить завдання поточному користувачу.

    :param request: Об'єкт HttpRequest.
    :param task_id: ID завдання, яке потрібно отримати.
    :type task_id: int
    :raises Http404: Якщо завдання не знайдено або не належить користувачу.
    :return: Об'єкт завдання.
    :rtype: TaskOut
    """
    user = get_current_user(request)
    task = get_object_or_404(Task, id=task_id, user=user)
    return task


# ОНОВЛЕННЯ (Update)
@task_router.post("/{task_id}/", response=TaskOut)
def update_task(request, task_id: int, payload: TaskIn):
    """
    Оновлює існуюче завдання за його ID.

    Дозволяє часткове оновлення (PATCH-подібна поведінка), оновлюючи
    лише ті поля, які були надані у 'payload'.

    :param request: Об'єкт HttpRequest.
    :param task_id: ID завдання, яке потрібно оновити.
    :type task_id: int
    :param payload: Дані для оновлення завдання.
    :type payload: TaskIn
    :raises Http404: Якщо завдання не знайдено або не належить користувачу.
    :return: Оновлений об'єкт завдання.
    :rtype: TaskOut
    """
    user = get_current_user(request)
    task = get_object_or_404(Task, id=task_id, user=user)

    # Оновлюємо поля моделі на основі даних з payload
    # exclude_unset=True гарантує, що ми оновлюємо лише ті поля, які були надані
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(task, attr, value)

    task.save()
    return task


# ВИДАЛЕННЯ (Delete)
@task_router.delete("/{task_id}/", response={204: None})
def delete_task(request, task_id: int):
    """
    Видаляє завдання за його ID.

    Перевіряє, чи належить завдання поточному користувачу перед видаленням.

    :param request: Об'єкт HttpRequest.
    :param task_id: ID завдання, яке потрібно видалити.
    :type task_id: int
    :raises Http404: Якщо завдання не знайдено або не належить користувачу.
    :status 204: Успішне видалення (без вмісту).
    :return: None.
    """
    user = get_current_user(request)
    task = get_object_or_404(Task, id=task_id, user=user)
    task.delete()
    return 204, None
