"""Read-only queries for the session cart, shared by views and the API."""

from decimal import Decimal
from typing import Any

from apps.catalog.models import Product
from apps.orders.cart import Cart


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
