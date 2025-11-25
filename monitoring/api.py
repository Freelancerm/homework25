from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from typing import List
from django.db import transaction
from .models import Server, Metric, AlertRule, AlertLog
from .schemas import *
from shared_auth.auth import bearer_auth

router = Router(tags=["Server Monitoring"])


def get_current_user(request):
    """
    Отримує автентифікованого користувача (User) з об'єкта запиту.

    В Django Ninja автентифікований об'єкт зберігається в 'request.auth'.

    :param request: Об'єкт HttpRequest.
    :return: Об'єкт моделі User.
    """
    return request.auth


# ==========================================================
#                  ЛОГІКА СПОВІЩЕНЬ (ALERTS)
# ==========================================================

def check_for_alerts(server: Server, payload: MetricIn):
    """
    Перевіряє надані метрики сервера на відповідність активним правилам сповіщень.

    Логіка перевірки:
    1. Перевіряє `status`: якщо False (DOWN), генерує сповіщення.
    2. Перевіряє числові метрики (CPU, Memory, Disk) на перевищення порогів,
       встановлених у моделі AlertRule для цього сервера.
    3. Якщо знайдено сповіщення, створює відповідні записи в AlertLog.

    :param server: Об'єкт моделі Server, до якого належать метрики.
    :type server: Server
    :param payload: Дані метрик, отримані від агента.
    :type payload: MetricIn
    :return: Список згенерованих повідомлень сповіщень.
    :rtype: list[str]
    """
    alerts = []

    # Перевірка статусу (якщо DOWN, завжди генеруємо сповіщення)
    if not payload.status:
        alerts.append(f"Server is DOWN!")

    # Перевірка числових метрик
    rules = AlertRule.objects.filter(server=server)

    metric_map = {
        'CPU_LOAD': payload.cpu_load,
        'MEMORY_USAGE': payload.memory_usage,
        'DISK_USAGE': payload.disk_usage,
    }

    for rule in rules:
        value = metric_map.get(rule.metric_name)
        if value is not None and value >= rule.threshold:
            alerts.append(
                f"{rule.metric_name} exceeded threshold! Value: {value:.2f}% (Threshold: {rule.threshold:.2f}%)")

    # Запис сповіщень до логу, якщо вони є
    if alerts:
        for msg in alerts:
            AlertLog.objects.create(server=server, message=msg)

    return alerts


# ==========================================================
#                      РОУТЕР СЕРВЕРІВ
# ==========================================================

# --- CRUD Серверів (вимагає авторизації) ---

@router.post("/servers/", response={201: ServerOut}, auth=bearer_auth)
def create_server(request, payload: ServerIn):
    """
    Реєструє новий сервер у системі моніторингу.

    Автоматично призначає поточного користувача як 'added_by'.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового сервера (назва, IP, опис).
    :type payload: ServerIn
    :status 201: Сервер успішно створено.
    :return: Об'єкт створеного сервера.
    :rtype: ServerOut
    """
    user = get_current_user(request)
    server = Server.objects.create(**payload.dict(), added_by=user)
    return 201, server


@router.get("/servers/", response=List[ServerOut], auth=bearer_auth)
def list_servers(request):
    """
    Повертає список усіх активних серверів.

    :param request: Об'єкт HttpRequest.
    :return: Список активних серверів.
    :rtype: List[ServerOut]
    """
    return Server.objects.filter(is_active=True)


@router.delete("/servers/{server_id}/", response={204: None}, auth=bearer_auth)
def delete_server(request, server_id: int):
    """
    Видаляє сервер.

    Доступно лише користувачу, який додав цей сервер (або користувачу з правами адміністратора,
    якщо логіка адміністрування була б імплементована).

    :param request: Об'єкт HttpRequest.
    :param server_id: ID сервера для видалення.
    :type server_id: int
    :raises Http404: Якщо сервер не знайдено або користувач не є 'added_by'.
    :status 204: Успішне видалення (без вмісту).
    :return: None.
    """
    # Може видалити тільки доданий ним сервер (або бути адміном)
    server = get_object_or_404(Server, id=server_id, added_by=get_current_user(request))
    server.delete()
    return 204, None


# ==========================================================
#                       РОУТЕР МЕТРИК
# ==========================================================

# Ендпоінт для надсилання даних моніторингу (імітує 'агента')
@router.post("/servers/{ip_address}/metrics/", response={201: MetricOut})
@transaction.atomic  # Забезпечуємо атомарність операцій
def submit_metrics(request, ip_address: str, payload: MetricIn):
    """
    Ендпоінт для надсилання даних моніторингу (імітує агента).

    1. Знаходить активний сервер за IP-адресою.
    2. Створює новий запис метрики.
    3. **Атомарно** викликає `check_for_alerts` для перевірки правил та генерації логів.

    :param request: Об'єкт HttpRequest.
    :param ip_address: IP-адреса сервера.
    :type ip_address: str
    :param payload: Дані метрик (CPU, Memory, Disk, Status).
    :type payload: MetricIn
    :raises Http404: Якщо активний сервер за IP-адресою не знайдено.
    :status 201: Метрики успішно збережено та оброблено.
    :return: Об'єкт створеної метрики.
    :rtype: MetricOut
    """

    server = get_object_or_404(Server, ip_address=ip_address, is_active=True)

    # 1. Створення запису метрики
    metric = Metric.objects.create(server=server, **payload.dict())

    # 2. Перевірка та генерація сповіщень
    check_for_alerts(server, payload)

    return 201, metric


@router.get("/servers/{ip_address}/metrics/latest/", response=MetricOut, auth=bearer_auth)
def get_latest_metrics(request, ip_address: str):
    """
    Повертає останній записаний набір метрик для заданого сервера.

    :param request: Об'єкт HttpRequest.
    :param ip_address: IP-адреса сервера.
    :type ip_address: str
    :raises Http404: Якщо сервер не знайдено або метрики відсутні.
    :return: Об'єкт останньої метрики.
    :rtype: MetricOut
    """
    server = get_object_or_404(Server, ip_address=ip_address)
    # Отримання останнього запису
    latest_metric = server.metrics.order_by('-timestamp').first()

    if not latest_metric:
        raise HttpError(404, "No metrics available")

    return latest_metric


# ==========================================================
#                   РОУТЕР ПРАВИЛ ТА ЛОГІВ
# ==========================================================

@router.post("/alerts/rules/{server_id}/", response={201: AlertRuleOut}, auth=bearer_auth)
def create_alert_rule(request, server_id: int, payload: AlertRuleIn):
    """
    Створює нове правило сповіщення або оновлює існуюче для конкретного сервера.

    Використовує `update_or_create` для уникнення дублювання правил
    за комбінацією (server, metric_name).

    :param request: Об'єкт HttpRequest.
    :param server_id: ID сервера, до якого застосовується правило.
    :type server_id: int
    :param payload: Дані правила (назва метрики, поріг).
    :type payload: AlertRuleIn
    :raises Http404: Якщо сервер не знайдено.
    :status 201: Правило успішно створено або оновлено.
    :return: Об'єкт правила сповіщення.
    :rtype: AlertRuleOut
    """
    server = get_object_or_404(Server, id=server_id)
    # Створюємо або оновлюємо правило, щоб уникнути дублювання
    rule, created = AlertRule.objects.update_or_create(
        server=server,
        metric_name=payload.metric_name,
        defaults={'threshold': payload.threshold}
    )
    return 201, rule


@router.get("/alerts/log/", response=List[AlertLogOut], auth=bearer_auth)
def list_alerts(request, is_resolved: Optional[bool] = False):
    """
    Повертає список усіх зареєстрованих сповіщень.

    Підтримує фільтрацію за статусом 'вирішено' (`is_resolved`).
    За замовчуванням повертає невирішені сповіщення.

    :param request: Об'єкт HttpRequest.
    :param is_resolved: Фільтр статусу вирішення (True, False або None для всіх).
    :type is_resolved: Optional[bool]
    :return: Список об'єктів логів сповіщень.
    :rtype: List[AlertLogOut]
    """
    queryset = AlertLog.objects.all().select_related('server').order_by('-created_at')

    if is_resolved is not None:
        queryset = queryset.filter(is_resolved=is_resolved)

    return queryset
