from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from apps.catalog.models import Category, Product


@pytest.mark.django_db
def test_category_str_and_default_parent() -> None:
    category = Category.objects.create(name='Electronics', slug='electronics')

    assert category.parent is None
    assert str(category) == 'Electronics'


@pytest.mark.django_db
def test_category_hierarchy_links_parent_and_children() -> None:
    parent = Category.objects.create(name='Electronics', slug='electronics')
    child = Category.objects.create(name='Phones', slug='phones', parent=parent)

    assert child.parent == parent
    assert list(parent.children.all()) == [child]


@pytest.mark.django_db
def test_category_slug_must_be_unique() -> None:
    Category.objects.create(name='Electronics', slug='shop')

    with pytest.raises(IntegrityError):
        Category.objects.create(name='Gadgets', slug='shop')


@pytest.mark.django_db
def test_product_stores_decimal_price_and_positive_stock() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='Good sound',
        price=Decimal('99.99'),
        category=category,
        stock=7,
    )

    assert product.price == Decimal('99.99')
    assert product.stock == 7
    assert product.is_active is True
    assert str(product) == 'Headphones'


@pytest.mark.django_db
def test_product_price_validator_rejects_zero() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('0'),
        category=category,
    )

    with pytest.raises(ValidationError):
        product.full_clean()


@pytest.mark.django_db
def test_product_negative_price_enforced_at_db_level() -> None:
    category = Category.objects.create(name='Shop', slug='shop')

    with pytest.raises(IntegrityError):
        Product.objects.create(
            name='Headphones',
            slug='headphones',
            description='',
            price=Decimal('-1.00'),
            category=category,
        )


@pytest.mark.django_db
def test_category_with_products_cannot_be_deleted() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('9.99'),
        category=category,
    )

    with pytest.raises(ProtectedError):
        category.delete()
