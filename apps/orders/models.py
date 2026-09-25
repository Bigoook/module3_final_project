from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class OrderNumber(models.Model):
    last = models.PositiveBigIntegerField(default=0)

    class Meta:
        verbose_name = _('order number counter')
        verbose_name_plural = _('order number counters')

    @classmethod
    def next(cls) -> int:
        with transaction.atomic():
            counter, _ = cls.objects.select_for_update().get_or_create(pk=1)
            counter.last += 1
            counter.save(update_fields=['last'])
            return counter.last


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', _('pending')
        PAID = 'paid', _('paid')
        SHIPPED = 'shipped', _('shipped')
        DELIVERED = 'delivered', _('delivered')
        CANCELLED = 'cancelled', _('cancelled')

    class PaymentMethod(models.TextChoices):
        CARD = 'card', _('card')
        CASH = 'cash', _('cash on delivery')
        BANK_TRANSFER = 'bank_transfer', _('bank transfer')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.PROTECT,
        related_name='orders',
    )
    order_number = models.PositiveBigIntegerField(_('order number'), unique=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_price = models.DecimalField(
        _('total price'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD,
    )
    full_name = models.CharField(_('full name'), max_length=255, blank=True, default='')
    email = models.EmailField(_('email'), blank=True, default='')
    phone = models.CharField(_('phone'), max_length=32, blank=True, default='')
    shipping_address = models.TextField(_('shipping address'), blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        constraints = (
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name='order_total_non_negative',
            ),
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.order_number:
            self.order_number = OrderNumber.next()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse('orders:order_detail', kwargs={'pk': self.pk})

    def __str__(self) -> str:
        return f'Order #{self.order_number}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name=_('order'),
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        'catalog.Product',
        verbose_name=_('product'),
        on_delete=models.PROTECT,
        related_name='order_items',
    )
    quantity = models.PositiveIntegerField(_('quantity'))
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_order_product',
            ),
            models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='item_price_positive',
            ),
        )
        ordering = ('pk',)
        verbose_name = _('item')
        verbose_name_plural = _('items')

    def __str__(self) -> str:
        return f'{self.order_id} / {self.product}'

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.price
