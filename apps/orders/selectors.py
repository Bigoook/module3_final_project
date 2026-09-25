"""Read-only queries for the session cart and order history."""

from decimal import Decimal
from typing import Any

from django.db.models import QuerySet

from apps.catalog.models import Product
from apps.orders.cart import Cart
from apps.orders.models import Order


def get_user_orders(user: Any, *, status: str = '') -> QuerySet[Order]:
    """The user's orders, optionally narrowed to one status."""
    queryset = Order.objects.filter(user=user).prefetch_related('items__product')
    if status and status in Order.Status.values:
        queryset = queryset.filter(status=status)
    return queryset


def get_cart_lines(cart: Cart) -> list[dict[str, Any]]:
    """Active cart rows with live prices, skipping products that are unavailable."""
    product_ids = [int(pk) for pk in cart.items()]
    products = {p.pk: p for p in Product.objects.filter(pk__in=product_ids, is_active=True)}
    lines = []
    for raw_pk, quantity in cart.items().items():
        product = products.get(int(raw_pk))
        if product is None:
            continue
        lines.append(
            {
                'product': product,
                'quantity': quantity,
                'line_total': product.price * Decimal(quantity),
            }
        )
    return lines


def get_cart_total(lines: list[dict[str, Any]]) -> Decimal:
    """Sum of already computed line totals, zero for an empty cart."""
    return sum((line['line_total'] for line in lines), Decimal('0'))
