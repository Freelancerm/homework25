from ninja import Schema
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


# Продукти
class ProductIn(Schema):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int
    is_active: Optional[bool] = True


class ProductOut(Schema):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    stock: int
    is_active: bool


# Кошик
class CartItemIn(Schema):
    product_id: int
    quantity: int = 1


class CartItemOut(Schema):
    id: int
    product_id: int
    product_name: str
    quantity: int

    @staticmethod
    def resolve_product_name(obj):
        return obj.product.name


class CartOut(Schema):
    id: int
    user_id: int
    items: List[CartItemOut]
    created_at: datetime


# Замовлення
class OrderIn(Schema):
    shipping_address: Optional[str] = "Стандартна адреса доставки"


class OrderItemOut(Schema):
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
    status: str # Очікуємо PENDING, SHIPPED, DELIVERED, CANCELED


class OrderOut(Schema):
    id: int
    user_id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemOut]