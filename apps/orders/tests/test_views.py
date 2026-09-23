from decimal import Decimal

import pytest
from django.contrib import messages
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.orders.cart import CART_SESSION_KEY


def _make_product(name: str = 'Alpha', stock: int = 5, price: str = '10.00') -> Product:
    category, _ = Category.objects.get_or_create(name='Shop', slug='shop')
    return Product.objects.create(
        name=name,
        slug=name.lower().replace(' ', '-'),
        description='',
        price=Decimal(price),
        category=category,
        stock=stock,
    )


def _add_url(product: Product) -> str:
    return reverse('orders:cart_add', kwargs={'product_id': product.pk})


def _cart_contents(response) -> dict[str, int]:
    session = response.wsgi_request.session
    return dict(session.get(CART_SESSION_KEY, {}))


@pytest.mark.django_db
def test_guest_can_add_to_cart(client) -> None:
    product = _make_product()

    response = client.post(_add_url(product), {'quantity': 2})

    assert response.status_code == 302
    assert response.url == product.get_absolute_url()
    assert _cart_contents(response)[str(product.pk)] == 2


@pytest.mark.django_db
def test_add_caps_quantity_at_stock(client) -> None:
    product = _make_product(stock=2)

    response = client.post(_add_url(product), {'quantity': 5})

    assert _cart_contents(response)[str(product.pk)] == 2
    assert any(
        m.level == messages.WARNING for m in messages.get_messages(response.wsgi_request)
    )


@pytest.mark.django_db
def test_add_out_of_stock_product_is_rejected(client) -> None:
    product = _make_product(stock=0)

    response = client.post(_add_url(product), {'quantity': 1})

    assert _cart_contents(response) == {}
    assert any(
        m.level == messages.ERROR for m in messages.get_messages(response.wsgi_request)
    )


@pytest.mark.django_db
def test_add_with_invalid_quantity_defaults_to_one(client) -> None:
    product = _make_product()

    response = client.post(_add_url(product), {'quantity': 0})

    assert _cart_contents(response)[str(product.pk)] == 1


@pytest.mark.django_db
def test_add_unknown_product_is_404(client) -> None:
    response = client.post(reverse('orders:cart_add', kwargs={'product_id': 9999}), {'quantity': 1})

    assert response.status_code == 404


@pytest.mark.django_db
def test_cart_page_lists_lines_and_total(client) -> None:
    product = _make_product(price='10.00')
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.get(reverse('orders:cart'))

    assert response.status_code == 200
    content = response.content.decode()
    assert 'Alpha' in content
    assert '$20.00' in content


@pytest.mark.django_db
def test_cart_page_shows_empty_state(client) -> None:
    response = client.get(reverse('orders:cart'))

    assert response.status_code == 200
    assert 'Your cart is empty.' in response.content.decode()


@pytest.mark.django_db
def test_update_changes_quantity(client) -> None:
    product = _make_product()
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.post(
        reverse('orders:cart_update', kwargs={'product_id': product.pk}),
        {'quantity': 4},
    )

    assert response.status_code == 302
    assert _cart_contents(response)[str(product.pk)] == 4


@pytest.mark.django_db
def test_update_caps_at_stock(client) -> None:
    product = _make_product(stock=3)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 1}
    session.save()

    client.post(
        reverse('orders:cart_update', kwargs={'product_id': product.pk}),
        {'quantity': 20},
    )

    session = client.session
    assert session[CART_SESSION_KEY][str(product.pk)] == 3


@pytest.mark.django_db
def test_update_out_of_stock_removes_line(client) -> None:
    product = _make_product(stock=0)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.post(
        reverse('orders:cart_update', kwargs={'product_id': product.pk}),
        {'quantity': 2},
    )

    reloaded = client.session.get(CART_SESSION_KEY, {})
    assert reloaded == {}
    assert any(
        m.level == messages.WARNING for m in messages.get_messages(response.wsgi_request)
    )


@pytest.mark.django_db
def test_update_unknown_line_is_rejected(client) -> None:
    product = _make_product()

    response = client.post(
        reverse('orders:cart_update', kwargs={'product_id': product.pk}),
        {'quantity': 3},
    )

    assert _cart_contents(response) == {}


@pytest.mark.django_db
def test_remove_deletes_line(client) -> None:
    product = _make_product()
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.post(reverse('orders:cart_remove', kwargs={'product_id': product.pk}))

    assert 'cart' not in response.wsgi_request.session or not response.wsgi_request.session.get('cart')


@pytest.mark.django_db
def test_cart_mutations_require_post(client) -> None:
    product = _make_product()

    assert client.get(_add_url(product)).status_code == 405
    assert client.get(reverse('orders:cart_update', kwargs={'product_id': product.pk})).status_code == 405
    assert client.get(reverse('orders:cart_remove', kwargs={'product_id': product.pk})).status_code == 405


@pytest.mark.django_db
def test_header_shows_cart_count(client) -> None:
    product = _make_product()
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 3}
    session.save()

    response = client.get(reverse('catalog:product_list'))

    assert response.context['cart_count'] == 3


@pytest.mark.django_db
def test_checkout_redirects_for_now(client) -> None:
    response = client.get(reverse('orders:checkout'))

    assert response.status_code == 302
    assert response.url == reverse('catalog:home')
