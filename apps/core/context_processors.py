"""Site-wide context available to every template."""

from django.conf import settings

from apps.catalog.models import Category
from apps.orders.cart import Cart


def main_context(request) -> dict[str, object]:
    return {
        'SHOP_NAME': settings.SHOP_NAME,
        'categories': Category.objects.filter(parent__isnull=True),
        'cart_count': Cart(request.session).count(),
    }
