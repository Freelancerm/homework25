from ninja.errors import HttpError
from ninja import Router
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import HttpRequest
from .models import Product, Cart, CartItem, Order, OrderItem
from .schemas import *
from .auth import AuthRequest
from shared_auth.auth import bearer_auth


# Helpers
def get_current_user(request):
    """
    Отримує автентифікованого користувача (User) з об'єкта запиту.

    В Django Ninja автентифікований об'єкт зберігається в 'request.auth'.

    :param request: Об'єкт HttpRequest.
    :return: Об'єкт моделі User.
    """
    return request.auth


# Роутер для Продуктів (CRUD)
# Захищено, оскільки змінювати товари має право лише адміністратор/авторизований персонал
product_router = Router(tags=['Products'], auth=bearer_auth)


@product_router.post("/", response={201: ProductOut})
def create_product(request: HttpRequest, payload: ProductIn):
    """
    Створює новий товар у каталозі.

    Цей ендпоінт захищений і доступний лише авторизованому персоналу.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового продукту.
    :type payload: ProductIn
    :status 201: Товар успішно створено.
    :return: Об'єкт створеного товару.
    :rtype: ProductOut
    """
    product = Product.objects.create(**payload.dict())
    return 201, product


@product_router.get("/{product_id}/", response={200: ProductOut})
def get_product(request: HttpRequest, product_id: int):
    """
    Повертає деталі активного товару за його ID.

    :param request: Об'єкт HttpRequest.
    :param product_id: ID товару.
    :type product_id: int
    :raises Http404: Якщо товар не знайдено або він не активний.
    :return: Об'єкт товару.
    :rtype: ProductOut
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    return product


@product_router.get("/", response=List[ProductOut])
def list_products(request: HttpRequest):
    """
    Повертає список усіх активних товарів у каталозі.

    :param request: Об'єкт HttpRequest.
    :return: Список активних товарів.
    :rtype: List[ProductOut]
    """
    return Product.objects.filter(is_active=True)


# Роутер для Кошика
cart_router = Router(tags=['Cart'], auth=bearer_auth)


@cart_router.get("/", response=CartOut)
def get_user_cart(request: AuthRequest):
    """
    Повертає кошик поточного автентифікованого користувача.

    Якщо кошик не існує, він створюється автоматично.

    :param request: Об'єкт AuthRequest (містить автентифікованого користувача).
    :return: Об'єкт кошика з його вмістом.
    :rtype: CartOut
    """
    user = request.auth
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


@cart_router.post("/items/", response=CartItemOut, auth=bearer_auth)
def add_to_cart(request: AuthRequest, payload: CartItemIn):
    """
    Додає товар до кошика або збільшує його кількість, якщо він вже є.

    :param request: Об'єкт AuthRequest.
    :param payload: Дані товару та кількості для додавання.
    :type payload: CartItemIn
    :raises Http404: Якщо товар не знайдено або він не активний.
    :raises HttpError 400: Якщо кількість не є позитивним числом.
    :return: Об'єкт CartItem, що відображає оновлений запис у кошику.
    :rtype: CartItemOut
    """
    user = request.auth
    cart, _ = Cart.objects.get_or_create(user=user)
    product = get_object_or_404(Product, id=payload.product_id, is_active=True)

    if payload.quantity <= 0:
        raise HttpError(400, "Значення кількості має бути позитивним")

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': payload.quantity}
    )
    if not created:
        item.quantity += payload.quantity
        item.save()

    return item


@cart_router.delete("/items/{item_id}/", response={204: None})
def remove_from_cart(request: AuthRequest, item_id: int):
    """
    Видаляє конкретний запис CartItem із кошика поточного користувача.

    :param request: Об'єкт AuthRequest.
    :param item_id: ID запису CartItem для видалення.
    :type item_id: int
    :raises Http404: Якщо CartItem не знайдено в кошику користувача.
    :status 204: Успішне видалення (без вмісту).
    :return: None.
    """
    user = request.auth
    cart = get_object_or_404(Cart, user=user)
    item = get_object_or_404(CartItem, cart=cart, id=item_id)
    item.delete()
    return 204, None


# Роутер для замовлень:
order_router = Router(tags=["Orders"], auth=bearer_auth)


@order_router.post("/checkout/", response={201: OrderOut})
@transaction.atomic
def create_order(request: AuthRequest):
    """
    Оформлює замовлення, перетворюючи вміст кошика на Order та OrderItem.

    Операція виконується в атомарній транзакції.
    Логіка включає:
    1. Перевірку наявності товарів у кошику.
    2. Перевірку достатньої кількості товарів на складі.
    3. Створення Order та OrderItem.
    4. Оновлення запасів товарів (зменшення stock).
    5. Очищення кошика.

    :param request: Об'єкт AuthRequest.
    :raises Http400: Якщо кошик порожній або недостатньо товару на складі.
    :status 201: Замовлення успішно створено.
    :return: Об'єкт створеного замовлення.
    :rtype: OrderOut
    """
    user = request.auth
    cart = get_object_or_404(Cart, user=user)
    cart_items = cart.items.select_related('product').all()

    if not cart_items:
        raise HttpError(400, 'Корзина порожня')

    total_amount = Decimal('0.00')

    # Створення об'єкта Замовлення
    order = Order.objects.create(
        user=user,
        total_amount=total_amount,
        status='PENDING'
    )

    order_items = []

    # Перенесення товарів з Кошика в Замовлення та розрахунок суми
    for item in cart_items:
        product = item.product
        if product.stock < item.quantity:
            raise HttpError(400, f"Цього товару недостатня к-сть в наявності: {product.name}")

        order_item = OrderItem(
            order=order,
            product=product,
            quantity=item.quantity,
            price_at_purchase=product.price
        )
        order_items.append(order_item)

        total_amount += product.price * item.quantity
        product.stock -= item.quantity
        product.save()

    OrderItem.objects.bulk_create(order_items)

    order.total_amount = total_amount
    order.save()

    cart_items.delete()

    return 201, order


@order_router.get("/", response=List[OrderOut])
def list_orders(request: AuthRequest):
    """
    Повертає список усіх замовлень, створених поточним користувачем.

    :param request: Об'єкт AuthRequest.
    :return: Список об'єктів замовлень.
    :rtype: List[OrderOut]
    """
    user = request.auth
    return Order.objects.filter(user=user).prefetch_related('items')


@order_router.put("/{order_id}/status/", response=OrderOut)
def update_order_status(request: AuthRequest, order_id: int, payload: OrderStatusUpdate):
    """
    Оновлює статус замовлення.

    Доступ до оновлення статусу обмежений:
    * Персонал (is_staff): може встановлювати будь-який допустимий статус для будь-якого замовлення.
    * Звичайний користувач: може скасувати ('CANCELED') лише власне замовлення, якщо воно в статусі 'PENDING'.

    :param request: Об'єкт AuthRequest.
    :param order_id: ID замовлення, статус якого потрібно оновити.
    :type order_id: int
    :param payload: Об'єкт, що містить новий статус.
    :type payload: OrderStatusUpdate
    :raises Http403: Якщо статус недійсний або користувач не має прав на цю дію.
    :raises Http404: Якщо замовлення не знайдено.
    :return: Оновлений об'єкт замовлення.
    :rtype: OrderOut
    """
    user = request.auth

    if payload.status not in ['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELED']:
        raise HttpError(403, 'Статус має бути: PENDING, SHIPPED, DELIVERED, CANCELED')
    elif user.is_staff:
        order = get_object_or_404(Order, id=order_id)
    elif payload.status == 'CANCELED':
        order = get_object_or_404(Order, id=order_id, user=user, status='PENDING')
    else:
        return HttpError(403, 'Forbidden or invalid action')

    order.status = payload.status
    order.save()
    return order
