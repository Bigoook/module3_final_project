from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.catalog.models import Category, Product
from apps.orders.services import (
    create_order,
    recalculate_total,
    remove_item,
    update_item_quantity,
)


def _make_category() -> Category:
    return Category.objects.create(name='Shop', slug='shop')


def _make_product(category: Category, name: str, price: str) -> Product:
    return Product.objects.create(
        name=name,
        description='',
        price=Decimal(price),
        category=category,
    )


@pytest.mark.django_db
def test_create_order_sums_subtotals_and_snapshots_prices() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    category = _make_category()
    first = _make_product(category, 'Alpha', '10.00')
    second = _make_product(category, 'Beta', '5.50')

    order = create_order(user=user, items=[(first, 2), (second, 3)], shipping_address='Kyiv')

    assert order.total_price == Decimal('36.50')
    items = {item.product_id: item for item in order.items.all()}
    assert items[first.pk].price == Decimal('10.00')
    assert items[first.pk].quantity == 2
    assert items[second.pk].price == Decimal('5.50')
    assert items[second.pk].quantity == 3


@pytest.mark.django_db
def test_update_quantity_recalculates_total() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    product = _make_product(_make_category(), 'Alpha', '10.00')
    order = create_order(user=user, items=[(product, 2)])

    update_item_quantity(order, product, 5)

    order.refresh_from_db()
    assert order.total_price == Decimal('50.00')


@pytest.mark.django_db
def test_remove_item_recalculates_total() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    category = _make_category()
    first = _make_product(category, 'Alpha', '10.00')
    second = _make_product(category, 'Beta', '5.00')
    order = create_order(user=user, items=[(first, 2), (second, 1)])

    remove_item(order, first)

    order.refresh_from_db()
    assert order.total_price == Decimal('5.00')


@pytest.mark.django_db
def test_removing_last_item_sets_total_to_zero() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    product = _make_product(_make_category(), 'Alpha', '10.00')
    order = create_order(user=user, items=[(product, 2)])

    remove_item(order, product)

    order.refresh_from_db()
    assert order.total_price == Decimal('0')


@pytest.mark.django_db
def test_recalculate_total_matches_summed_subtotals() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    category = _make_category()
    first = _make_product(category, 'Alpha', '10.00')
    second = _make_product(category, 'Beta', '5.50')
    order = create_order(user=user, items=[(first, 3), (second, 4)])

    expected = sum(item.subtotal for item in order.items.all())

    recalculate_total(order)
    order.refresh_from_db()

    assert order.total_price == expected


@pytest.mark.django_db
def test_order_reuses_order_number_counter() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    product = _make_product(_make_category(), 'Alpha', '1.00')

    first = create_order(user=user, items=[(product, 1)])
    second = create_order(user=user, items=[(product, 1)])

    assert first.order_number
    assert second.order_number == first.order_number + 1
