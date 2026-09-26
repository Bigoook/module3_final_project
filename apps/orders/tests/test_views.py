from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.factories import make_product
from apps.orders.cart import CART_SESSION_KEY
from apps.orders.models import Order


def _add_url(product) -> str:
    return reverse('orders:cart_add', kwargs={'product_id': product.pk})


def _cart_contents(response) -> dict[str, int]:
    session = response.wsgi_request.session
    return dict(session.get(CART_SESSION_KEY, {}))


@pytest.mark.django_db
def test_guest_can_add_to_cart(client) -> None:
    product = make_product()

    response = client.post(_add_url(product), {'quantity': 2})

    assert response.status_code == 302
    assert response.url == product.get_absolute_url()
    assert _cart_contents(response)[str(product.pk)] == 2


@pytest.mark.django_db
def test_add_caps_quantity_at_stock(client) -> None:
    product = make_product(stock=2)

    response = client.post(_add_url(product), {'quantity': 5})

    assert _cart_contents(response)[str(product.pk)] == 2
    assert any(m.level == messages.WARNING for m in messages.get_messages(response.wsgi_request))


@pytest.mark.django_db
def test_add_out_of_stock_product_is_rejected(client) -> None:
    product = make_product(stock=0)

    response = client.post(_add_url(product), {'quantity': 1})

    assert _cart_contents(response) == {}
    assert any(m.level == messages.ERROR for m in messages.get_messages(response.wsgi_request))


@pytest.mark.django_db
def test_add_with_invalid_quantity_defaults_to_one(client) -> None:
    product = make_product()

    response = client.post(_add_url(product), {'quantity': 0})

    assert _cart_contents(response)[str(product.pk)] == 1


@pytest.mark.django_db
def test_add_unknown_product_is_404(client) -> None:
    response = client.post(reverse('orders:cart_add', kwargs={'product_id': 9999}), {'quantity': 1})

    assert response.status_code == 404


@pytest.mark.django_db
def test_cart_page_lists_lines_and_total(client) -> None:
    product = make_product(price='10.00')
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
    product = make_product()
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
    product = make_product(stock=3)
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
    product = make_product(stock=0)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.post(
        reverse('orders:cart_update', kwargs={'product_id': product.pk}),
        {'quantity': 2},
    )

    reloaded = client.session.get(CART_SESSION_KEY, {})
    assert reloaded == {}
    assert any(m.level == messages.WARNING for m in messages.get_messages(response.wsgi_request))


@pytest.mark.django_db
def test_update_unknown_line_is_rejected(client) -> None:
    product = make_product()

    response = client.post(
        reverse('orders:cart_update', kwargs={'product_id': product.pk}),
        {'quantity': 3},
    )

    assert _cart_contents(response) == {}


@pytest.mark.django_db
def test_remove_deletes_line(client) -> None:
    product = make_product()
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.post(reverse('orders:cart_remove', kwargs={'product_id': product.pk}))

    assert 'cart' not in response.wsgi_request.session or not response.wsgi_request.session.get('cart')


@pytest.mark.django_db
def test_cart_mutations_require_post(client) -> None:
    product = make_product()

    assert client.get(_add_url(product)).status_code == 405
    assert client.get(reverse('orders:cart_update', kwargs={'product_id': product.pk})).status_code == 405
    assert client.get(reverse('orders:cart_remove', kwargs={'product_id': product.pk})).status_code == 405


@pytest.mark.django_db
def test_header_shows_cart_count(client) -> None:
    product = make_product()
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 3}
    session.save()

    response = client.get(reverse('catalog:product_list'))

    assert response.context['cart_count'] == 3


@pytest.mark.django_db
def test_checkout_requires_login(client) -> None:
    response = client.get(reverse('orders:checkout'))

    assert response.status_code == 302
    assert reverse('accounts:login') in response.url


@pytest.mark.django_db
def test_checkout_with_empty_cart_redirects_to_cart(client) -> None:
    user = get_user_model().objects.create_user(username='buyer', password='pass')
    client.force_login(user)

    response = client.get(reverse('orders:checkout'))

    assert response.status_code == 302
    assert response.url == reverse('orders:cart')


@pytest.mark.django_db
def test_checkout_invalid_form_rerenders_without_creating_order(client) -> None:
    user = get_user_model().objects.create_user(username='buyer', password='pass')
    client.force_login(user)
    product = make_product(stock=5)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.post(
        reverse('orders:checkout'),
        {
            'full_name': 'A',
            'email': 'not-an-email',
            'phone': 'x',
            'shipping_address': 'Kyiv',
            'payment_method': 'card',
        },
    )

    assert response.status_code == 200
    assert Order.objects.count() == 0
    product.refresh_from_db()
    assert product.stock == 5


@pytest.mark.django_db
def test_checkout_prefills_fields_from_user_profile(client) -> None:
    user = get_user_model().objects.create_user(
        username='buyer',
        password='pass',
        email='buyer@example.com',
        first_name='Test',
        last_name='Buyer',
        phone='+380 12 345 67 89',
        default_address='Khreshchatyk 1, Kyiv',
    )
    client.force_login(user)
    product = make_product(stock=5)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.get(reverse('orders:checkout'))

    assert response.status_code == 200
    form = response.context['form']
    assert form.initial['full_name'] == 'Test Buyer'
    assert form['full_name'].value() == 'Test Buyer'
    assert form['email'].value() == 'buyer@example.com'
    assert form['phone'].value() == '+380 12 345 67 89'
    assert form['shipping_address'].value() == 'Khreshchatyk 1, Kyiv'


@pytest.mark.django_db
def test_checkout_form_does_not_show_blank_full_name(client) -> None:
    user = get_user_model().objects.create_user(username='buyer', password='pass')
    client.force_login(user)
    product = make_product(stock=5)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.get(reverse('orders:checkout'))

    form = response.context['form']
    assert not form['full_name'].value()
    assert not form['shipping_address'].value()


@pytest.mark.django_db
@patch('apps.orders.views.send_order_confirmation')
def test_checkout_places_order_and_clears_cart(send_mock, client) -> None:
    user = get_user_model().objects.create_user(username='buyer', password='pass')
    client.force_login(user)
    product = make_product(name='Cascade', price='10.00', stock=5)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 2}
    session.save()

    response = client.post(
        reverse('orders:checkout'),
        {
            'full_name': 'Test Buyer',
            'email': 'buyer@example.com',
            'phone': '+380 12 345 67 89',
            'shipping_address': 'Khreshchatyk 1, Kyiv',
            'payment_method': 'card',
        },
    )

    assert response.status_code == 302
    order = Order.objects.get()
    assert order.user == user
    assert order.total_price == Decimal('20.00')
    assert order.full_name == 'Test Buyer'
    assert order.email == 'buyer@example.com'
    assert order.payment_method == 'card'
    assert order.items.count() == 1
    assert order.items.get().price == Decimal('10.00')
    assert response.url == reverse('orders:order_detail', kwargs={'pk': order.pk})
    assert client.session.get(CART_SESSION_KEY, {}) == {}
    product.refresh_from_db()
    assert product.stock == 3
    send_mock.assert_called_once_with(order)


@pytest.mark.django_db
@patch('apps.orders.views.send_order_confirmation')
def test_checkout_out_of_stock_rerenders_transaction_rolled_back(send_mock, client) -> None:
    user = get_user_model().objects.create_user(username='buyer', password='pass')
    client.force_login(user)
    product = make_product(name='Mosaic', stock=2)
    session = client.session
    session[CART_SESSION_KEY] = {str(product.pk): 10}
    session.save()

    response = client.post(
        reverse('orders:checkout'),
        {
            'full_name': 'Test Buyer',
            'email': 'buyer@example.com',
            'phone': '+380 12 345 67 89',
            'shipping_address': 'Khreshchatyk 1, Kyiv',
            'payment_method': 'card',
        },
    )

    assert response.status_code == 200
    assert Order.objects.count() == 0
    assert any(m.level == messages.ERROR for m in messages.get_messages(response.wsgi_request))
    product.refresh_from_db()
    assert product.stock == 2
    send_mock.assert_not_called()


@pytest.mark.django_db
def test_order_detail_is_owner_only(client) -> None:
    owner = get_user_model().objects.create_user(username='owner', password='pass')
    other = get_user_model().objects.create_user(username='other', password='pass')
    order = Order.objects.create(
        user=owner,
        full_name='Owner',
        email='owner@example.com',
        phone='+380 12 345 67 89',
    )

    client.force_login(other)
    assert client.get(reverse('orders:order_detail', kwargs={'pk': order.pk})).status_code == 404

    client.force_login(owner)
    response = client.get(reverse('orders:order_detail', kwargs={'pk': order.pk}))
    assert response.status_code == 200
    assert f'Order #{order.order_number}' in response.content.decode()
