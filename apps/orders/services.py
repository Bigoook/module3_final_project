"""Order operations that keep Order.total_price in sync with its items."""

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce

from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem


def recalculate_total(order: Order) -> None:
    """Recompute Order.total_price from its items and persist it."""
    total = order.items.aggregate(
        total=Coalesce(
            Sum(
                F('quantity') * F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
            Value(Decimal('0')),
        )
    )['total']
    order.total_price = Decimal(total)
    order.save(update_fields=['total_price'])


@transaction.atomic
def create_order(
    *,
    user: Any,
    items: Sequence[tuple[Product, int]],
    shipping_address: str = '',
) -> Order:
    """Create an order with items, snapshotting product prices and summing total."""
    order = Order.objects.create(
        user=user,
        total_price=Decimal('0'),
        shipping_address=shipping_address,
    )
    for product, quantity in items:
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
        )
    recalculate_total(order)
    return order


def update_item_quantity(order: Order, product: Product, quantity: int) -> None:
    """Change how many units of ``product`` are in the order, then recalc total."""
    item = order.items.filter(product=product).first()
    if item is not None:
        item.quantity = quantity
        item.save(update_fields=['quantity'])
        recalculate_total(order)


def remove_item(order: Order, product: Product) -> None:
    """Drop ``product`` from the order, then recalc total."""
    order.items.filter(product=product).delete()
    recalculate_total(order)
