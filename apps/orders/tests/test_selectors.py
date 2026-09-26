from decimal import Decimal

import pytest

from apps.factories import make_product
from apps.orders.cart import Cart
from apps.orders.selectors import get_cart_lines, get_cart_total


class _FakeSession(dict):
    modified = False


def _make_cart() -> Cart:
    return Cart(_FakeSession())


@pytest.mark.django_db
def test_get_cart_lines_carry_live_prices() -> None:
    product = make_product(price='10.00')
    cart = _make_cart()
    cart.add(product.pk, 2)

    lines = get_cart_lines(cart)

    assert len(lines) == 1
    assert lines[0]['product'].pk == product.pk
    assert lines[0]['quantity'] == 2
    assert lines[0]['line_total'] == Decimal('20.00')


@pytest.mark.django_db
def test_get_cart_lines_skip_inactive_products() -> None:
    active = make_product(name='Alpha', price='10.00')
    hidden = make_product(name='Hidden', price='5.00')
    hidden.is_active = False
    hidden.save()
    cart = _make_cart()
    cart.add(active.pk, 2)
    cart.add(hidden.pk, 1)

    lines = get_cart_lines(cart)

    assert len(lines) == 1
    assert lines[0]['product'].pk == active.pk


@pytest.mark.django_db
def test_get_cart_lines_skip_deleted_products() -> None:
    product = make_product()
    cart = _make_cart()
    cart.add(product.pk, 2)
    product.delete()

    assert get_cart_lines(cart) == []


@pytest.mark.django_db
def test_get_cart_total_sums_line_totals() -> None:
    first = make_product(name='Alpha', price='10.00')
    second = make_product(name='Beta', price='5.50')
    cart = _make_cart()
    cart.add(first.pk, 2)
    cart.add(second.pk, 3)

    total = get_cart_total(get_cart_lines(cart))

    assert total == Decimal('36.50')


def test_get_cart_total_of_empty_cart_is_zero() -> None:
    assert get_cart_total([]) == Decimal('0')
