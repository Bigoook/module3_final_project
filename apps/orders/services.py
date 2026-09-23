"""Order and cart operations that keep totals in sync with their items."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from django.db import transaction
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce

from apps.catalog.models import Product
from apps.orders.cart import Cart
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


class CartStatus(StrEnum):
    """Vocabulary of outcomes shared by cart services and their callers."""

    ADDED = 'added'
    CAPPED = 'capped'
    OUT_OF_STOCK = 'out_of_stock'
    MISSING = 'missing'
    REMOVED = 'removed'
    UPDATED = 'updated'


@dataclass(frozen=True)
class CartActionResult:
    """Outcome of a cart mutation and the quantity it settled on."""

    status: CartStatus
    quantity: int


def add_product_to_cart(cart: Cart, product: Product, quantity: int) -> CartActionResult:
    """Add units up to the available stock; returns whether units were added or capped."""
    if product.stock == 0:
        return CartActionResult(status=CartStatus.OUT_OF_STOCK, quantity=0)
    added = min(quantity, product.stock)
    cart.add(product.pk, added)
    status = CartStatus.ADDED if added == quantity else CartStatus.CAPPED
    return CartActionResult(status=status, quantity=added)


def update_cart_quantity(cart: Cart, product: Product, quantity: int) -> CartActionResult:
    """Set an exact quantity capped at stock; removes lines that went out of stock."""
    if not cart.contains(product.pk):
        return CartActionResult(status=CartStatus.MISSING, quantity=0)
    if product.stock == 0:
        cart.remove(product.pk)
        return CartActionResult(status=CartStatus.REMOVED, quantity=0)
    capped = min(quantity, product.stock)
    cart.set_quantity(product.pk, capped)
    status = CartStatus.UPDATED if capped == quantity else CartStatus.CAPPED
    return CartActionResult(status=status, quantity=capped)


def remove_from_cart(cart: Cart, product: Product) -> None:
    """Drop the product's line from the cart; safe when it is not present."""
    cart.remove(product.pk)
