from django.db import models
from django.contrib.auth.models import User


# Продукти
class Product(models.Model):
    """ Модель, що представляє товар у каталозі магазину. """
    name = models.CharField(max_length=255)
    """ Назва товару. """

    description = models.TextField(blank=True)
    """ Детальний опис товару (необов'язково) """

    price = models.DecimalField(max_digits=10, decimal_places=2)
    """ Ціна товару. """

    stock = models.IntegerField(default=0)
    """ Кількість товару в наявності на складі. """

    is_active = models.BooleanField(default=True)
    """
    Статус активності: визначає, чи відображається товар у каталозі. 
    За замовчуванням: True. 
    """

    def __str__(self):
        """Повертає назву товару."""
        return self.name


# Кошик (прив'язаний до користувача)
class Cart(models.Model):
    """
    Модель, що представляє кошик покупця.

    Кожен користувач може мати лише один активний кошик.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    """ 
    Зв'язок "один-до-одного" з моделлю користувача.
    Видалення користувача призводить до видалення кошика.
    Зворотна назва зв'язку: 'cart'.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    """ Дата та час створення кошика. """

    def __str__(self):
        """ Повертає ідентифікатор кошика та ім'я користувача. """
        return f"Кошик користувача: {self.user.username}"


# Елементи кошика:
class CartItem(models.Model):
    """ Елемент (позиція) у кошику, що містить посилання на товар та його кількість. """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')

    """ Зовнішній ключ на кошик, до якого належить елемент. """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    """ Зовнішній ключ на товар, доданий у кошик. """

    quantity = models.IntegerField(default=1)
    """ Кількість цього товару у кошику. """

    class Meta:
        """
        Обмеження унікальності: гарантує, що один і той же товар
        може бути доданий лише один раз в межах одного кошика.
        """
        unique_together = ('cart', 'product')  # Один продукт - одна позиція в кошику

    def __str__(self):
        """ Повертає кількість та назву товару. """
        return f"{self.quantity} x {self.product.name}"


# Замовлення
class Order(models.Model):
    """ Модель, що представляє фінальне замовлення користувача. """
    STATUS_CHOICES = (
        ('PENDING', 'У процесі'),
        ('SHIPPED', 'Відправлений'),
        ('DELIVERED', 'Доставлений'),
        ('CANCELED', 'Скасований'),
    )
    """ Можливі статуси замовлення. """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    """ Користувач, який оформив замовлення. """

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    """ Поточний статус замовлення. """

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    """ Загальна сума замовлення. """

    created_at = models.DateTimeField(auto_now_add=True)
    """ Дата та час створення замовлення. """

    def __str__(self):
        """ Повертає номер замовлення та його поточний статус. """
        return f"Номер замовлення #{self.id} ({self.status})"


# Елементи замовлення
class OrderItem(models.Model):
    """
    Елемент (позиція) у замовленні.

    Зберігає статичну ціну товару на момент покупки (price_at_purchase),
    що є критичним для збереження історії транзакцій.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    """ Зовнішній ключ на замовлення, до якого належить елемент. """

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    """ Зовнішній ключ на товар. """

    quantity = models.PositiveIntegerField(default=1)
    """ Кількість цього товару в замовленні. """

    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    """
    Ціна товару на момент створення замовлення. 
    Це важливо, оскільки ціна товару може змінюватися пізніше.
    """

    def __str__(self):
        """ Повертає кількість, назву товару та номер замовлення. """
        return f"{self.quantity} x {self.product.name} для Замовлення #{self.order.id}"
