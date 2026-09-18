from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.catalog.models import Category, Product
from apps.orders.models import Order, OrderItem


@pytest.mark.django_db
def test_order_default_status_is_pending() -> None:
    user = get_user_model().objects.create(username='buyer')
    order = Order.objects.create(user=user, total_price=Decimal('0'))

    assert order.status == Order.Status.PENDING


@pytest.mark.django_db
def test_order_item_calculates_subtotal() -> None:
    user = get_user_model().objects.create(username='buyer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('10.00'),
        category=category,
    )
    order = Order.objects.create(user=user, total_price=Decimal('0'))
    item = OrderItem.objects.create(order=order, product=product, quantity=3, price=Decimal('4.00'))

    assert item.subtotal == Decimal('12.00')


@pytest.mark.django_db
def test_order_item_is_unique_per_product() -> None:
    user = get_user_model().objects.create(username='buyer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('10.00'),
        category=category,
    )
    order = Order.objects.create(user=user, total_price=Decimal('0'))
    OrderItem.objects.create(order=order, product=product, quantity=1, price=Decimal('1.00'))

    with pytest.raises(IntegrityError):
        OrderItem.objects.create(order=order, product=product, quantity=2, price=Decimal('2.00'))


@pytest.mark.django_db
def test_deleting_order_cascades_to_items() -> None:
    user = get_user_model().objects.create(username='buyer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('10.00'),
        category=category,
    )
    order = Order.objects.create(user=user, total_price=Decimal('0'))
    OrderItem.objects.create(order=order, product=product, quantity=1, price=Decimal('1.00'))

    order.delete()

    assert OrderItem.objects.filter(order_id=order.pk).count() == 0


@pytest.mark.django_db
def test_order_item_price_validator_rejects_zero() -> None:
    user = get_user_model().objects.create(username='buyer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('10.00'),
        category=category,
    )
    order = Order.objects.create(user=user, total_price=Decimal('0'))
    item = OrderItem(order=order, product=product, quantity=1, price=Decimal('0'))

    with pytest.raises(ValidationError):
        item.full_clean()


@pytest.mark.django_db
def test_order_item_negative_price_enforced_at_db_level() -> None:
    user = get_user_model().objects.create(username='buyer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('10.00'),
        category=category,
    )
    order = Order.objects.create(user=user, total_price=Decimal('0'))

    with pytest.raises(IntegrityError):
        OrderItem.objects.create(order=order, product=product, quantity=1, price=Decimal('-1.00'))


@pytest.mark.django_db
def test_order_negative_total_price_enforced_at_db_level() -> None:
    user = get_user_model().objects.create(username='buyer')

    with pytest.raises(IntegrityError):
        Order.objects.create(user=user, total_price=Decimal('-5.00'))


@pytest.mark.django_db
def test_order_number_increments_and_is_not_reused() -> None:
    user = get_user_model().objects.create(username='buyer')
    first = Order.objects.create(user=user, total_price=Decimal('0'))
    second = Order.objects.create(user=user, total_price=Decimal('0'))

    assert first.order_number == 1
    assert second.order_number == 2
    assert str(first) == 'Order #1'

    second.delete()
    third = Order.objects.create(user=user, total_price=Decimal('0'))

    assert third.order_number == 3
