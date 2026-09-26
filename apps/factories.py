"""Shared model factories for tests (kept outside ``tests/`` so pytest skips them)."""

from decimal import Decimal
from typing import Any

from apps.catalog.models import Category, Product


def make_category(name: str = 'Shop', slug: str = 'shop') -> Category:
    return Category.objects.create(name=name, slug=slug)


def make_product(
    name: str = 'Alpha',
    category: Category | None = None,
    price: str | Decimal = '10.00',
    stock: int = 5,
    is_active: bool = True,
    description: str = '',
    **kwargs: Any,
) -> Product:
    if category is None:
        category, _ = Category.objects.get_or_create(name='Shop', slug='shop')
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        description=description,
        price=Decimal(price),
        category=category,
        stock=stock,
        is_active=is_active,
        **kwargs,
    )
