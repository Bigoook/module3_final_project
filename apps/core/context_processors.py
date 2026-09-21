"""Site-wide context available to every template."""

from apps.catalog.models import Category

SHOP_NAME = 'Brew & Barrel'


def main_context(request) -> dict[str, object]:
    return {
        'SHOP_NAME': SHOP_NAME,
        'categories': Category.objects.filter(parent__isnull=True),
        'cart_count': 0,
    }
