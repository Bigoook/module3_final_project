from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.factories import make_category, make_product
from apps.orders.cart import Cart
from apps.orders.models import Order
from apps.orders.services import (
    CartStatus,
    OutOfStockError,
    add_product_to_cart,
    create_order,
    recalculate_total,
    remove_from_cart,
    remove_item,
    update_cart_quantity,
    update_item_quantity,
)


class _FakeSession(dict):
    modified = False


@pytest.mark.django_db
def test_create_order_sums_subtotals_and_snapshots_prices() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    category = make_category()
    first = make_product(category=category, name='Alpha', price='10.00')
    second = make_product(category=category, name='Beta', price='5.50')

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
    product = make_product(name='Alpha', price='10.00')
    order = create_order(user=user, items=[(product, 2)])

    update_item_quantity(order, product, 5)

    order.refresh_from_db()
    assert order.total_price == Decimal('50.00')


@pytest.mark.django_db
def test_remove_item_recalculates_total() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    category = make_category()
    first = make_product(category=category, name='Alpha', price='10.00')
    second = make_product(category=category, name='Beta', price='5.00')
    order = create_order(user=user, items=[(first, 2), (second, 1)])

    remove_item(order, first)

    order.refresh_from_db()
    assert order.total_price == Decimal('5.00')


@pytest.mark.django_db
def test_removing_last_item_sets_total_to_zero() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    product = make_product(name='Alpha', price='10.00')
    order = create_order(user=user, items=[(product, 2)])

    remove_item(order, product)

    order.refresh_from_db()
    assert order.total_price == Decimal('0')


@pytest.mark.django_db
def test_recalculate_total_matches_summed_subtotals() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    category = make_category()
    first = make_product(category=category, name='Alpha', price='10.00')
    second = make_product(category=category, name='Beta', price='5.50')
    order = create_order(user=user, items=[(first, 3), (second, 4)])

    expected = sum(item.subtotal for item in order.items.all())

    recalculate_total(order)
    order.refresh_from_db()

    assert order.total_price == expected


@pytest.mark.django_db
def test_order_reuses_order_number_counter() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    product = make_product(name='Alpha', price='1.00')

    first = create_order(user=user, items=[(product, 1)])
    second = create_order(user=user, items=[(product, 1)])

    assert first.order_number
    assert second.order_number == first.order_number + 1


@pytest.mark.django_db
def test_create_order_decrements_product_stock() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    product = make_product(name='Alpha', price='10.00', stock=5)

    create_order(user=user, items=[(product, 2)])

    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.django_db
def test_create_order_out_of_stock_rolls_back() -> None:
    user = get_user_model().objects.create_user(username='buyer')
    product = make_product(name='Alpha', price='10.00', stock=2)

    with pytest.raises(OutOfStockError):
        create_order(user=user, items=[(product, 5)])

    assert Order.objects.count() == 0
    product.refresh_from_db()
    assert product.stock == 2


@pytest.mark.django_db
def test_add_product_to_cart_returns_added() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00', stock=5)

    result = add_product_to_cart(cart, product, 3)

    assert result.status == CartStatus.ADDED
    assert result.quantity == 3
    assert cart.get_quantity(product.pk) == 3


@pytest.mark.django_db
def test_add_product_to_cart_caps_at_stock() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00', stock=2)

    result = add_product_to_cart(cart, product, 5)

    assert result.status == CartStatus.CAPPED
    assert result.quantity == 2
    assert cart.get_quantity(product.pk) == 2


@pytest.mark.django_db
def test_add_product_to_cart_rejects_out_of_stock() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00', stock=0)

    result = add_product_to_cart(cart, product, 1)

    assert result.status == CartStatus.OUT_OF_STOCK
    assert result.quantity == 0
    assert not cart.contains(product.pk)


@pytest.mark.django_db
def test_update_cart_quantity_sets_exact_quantity() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00', stock=10)
    cart.add(product.pk, 2)

    result = update_cart_quantity(cart, product, 7)

    assert result.status == CartStatus.UPDATED
    assert result.quantity == 7
    assert cart.get_quantity(product.pk) == 7


@pytest.mark.django_db
def test_update_cart_quantity_caps_at_stock() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00', stock=4)
    cart.add(product.pk, 2)

    result = update_cart_quantity(cart, product, 20)

    assert result.status == CartStatus.CAPPED
    assert result.quantity == 4
    assert cart.get_quantity(product.pk) == 4


@pytest.mark.django_db
def test_update_cart_quantity_removes_out_of_stock_line() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00', stock=0)
    cart.add(product.pk, 2)

    result = update_cart_quantity(cart, product, 2)

    assert result.status == CartStatus.REMOVED
    assert not cart.contains(product.pk)


@pytest.mark.django_db
def test_update_cart_quantity_missing_line_is_rejected() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00')

    result = update_cart_quantity(cart, product, 2)

    assert result.status == CartStatus.MISSING
    assert cart.count() == 0


@pytest.mark.django_db
def test_remove_from_cart_drops_line() -> None:
    cart = Cart(_FakeSession())
    product = make_product(name='Alpha', price='10.00')
    cart.add(product.pk, 3)

    remove_from_cart(cart, product)

    assert not cart.contains(product.pk)
