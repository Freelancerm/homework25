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
    return request.auth


# Роутер для Продуктів (CRUD)
# Захищено, оскільки змінювати товари має право лише адміністратор/авторизований персонал
product_router = Router(tags=['Products'], auth=bearer_auth)


@product_router.post("/", response={201: ProductOut})
def create_product(request: HttpRequest, payload: ProductIn):
    product = Product.objects.create(**payload.dict())
    return 201, product


@product_router.get("/{product_id}/", response={200: ProductOut})
def get_product(request: HttpRequest, product_id: int):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    return product


@product_router.get("/", response=List[ProductOut])
def list_products(request: HttpRequest):
    return Product.objects.filter(is_active=True)


# Роутер для Кошика
cart_router = Router(tags=['Cart'], auth=bearer_auth)


@cart_router.get("/", response=CartOut)
def get_user_cart(request: AuthRequest):
    user = request.auth
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


@cart_router.post("/items/", response=CartItemOut, auth=bearer_auth)
def add_to_cart(request: AuthRequest, payload: CartItemIn):
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
    user = request.auth
    return Order.objects.filter(user=user).prefetch_related('items')


@order_router.put("/{order_id}/status/", response=OrderOut)
def update_order_status(request: AuthRequest, order_id: int, payload: OrderStatusUpdate):
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
