from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('pending')
        PAID = 'paid', _('paid')
        SHIPPED = 'shipped', _('shipped')
        DELIVERED = 'delivered', _('delivered')
        CANCELLED = 'cancelled', _('cancelled')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.PROTECT,
        related_name='orders',
    )
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
    )
    shipping_address = models.TextField(_('shipping address'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self) -> str:
        return f'Order #{self.pk}'


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
        related_name='items',
    )
    quantity = models.PositiveIntegerField(_('quantity'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_order_product',
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
