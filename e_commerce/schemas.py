from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


# Продукти
class ProductIn(Schema):
    """
    Схема вхідних даних для створення або оновлення об'єкта Product.

    Використовується для валідації даних, що надходять у тілі POST/PUT запиту.
    """
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int
    is_active: Optional[bool] = True


class ProductOut(Schema):
    """ Схема вихідних даних для представлення об'єкта Product у відповіді API. """
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    stock: int
    is_active: bool


# Кошик
class CartItemIn(Schema):
    """ Схема вхідних даних для додавання товару до кошика. """
    product_id: int
    quantity: int = 1


class CartItemOut(Schema):
    """ Схема вихідних даних для представлення елемента CartItem. """
    id: int
    product_id: int
    product_name: str
    quantity: int

    @staticmethod
    def resolve_product_name(obj):
        return obj.product.name


class CartOut(Schema):
    """ Схема вихідних даних для представлення об'єкта Cart (кошика). """
    id: int
    user_id: int
    items: List[CartItemOut]
    created_at: datetime


# Замовлення
class OrderIn(Schema):
    """ Схема вхідних даних для оформлення нового замовлення (Checkout). """
    shipping_address: Optional[str] = "Стандартна адреса доставки"


class OrderItemOut(Schema):
    """ Схема вихідних даних для представлення елемента замовлення (OrderItem). """
    product_name: str
    quantity: int
    price_at_purchase: Decimal

    @staticmethod
    def resolve_product_name(obj):
        return obj.product.name

    @staticmethod
    def resolve_quantity(obj):
        return obj.quantity

    @staticmethod
    def resolve_price_at_purchase(obj):
        return obj.price_at_purchase


class OrderStatusUpdate(Schema):
    """ Схема вхідних даних для оновлення статусу існуючого замовлення. """
    status: str  # Очікуємо PENDING, SHIPPED, DELIVERED, CANCELED


class OrderOut(Schema):
    """ Схема вихідних даних для представлення об'єкта Order (замовлення). """
    id: int
    user_id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemOut]
