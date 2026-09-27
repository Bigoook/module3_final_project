from collections.abc import Iterator

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import translation

from apps.factories import make_product
from apps.orders.models import Order
from apps.orders.services import OrderTransitionError, OutOfStockError, cancel_order

pytestmark = pytest.mark.django_db

UK_PREFIX = '/uk'


@pytest.fixture(autouse=True)
def _restore_default_language() -> Iterator[None]:
    yield
    translation.activate(settings.LANGUAGE_CODE)


def _order(status: Order.Status = Order.Status.PENDING) -> Order:
    user = get_user_model().objects.create_user(username=f'user-{status}')
    return Order.objects.create(
        user=user,
        order_number=1000 + user.pk,
        status=status,
        full_name='Test',
        email='test@example.com',
        shipping_address='Kyiv',
    )


def test_default_language_urls_have_no_prefix() -> None:
    assert reverse('catalog:home') == '/'
    assert reverse('catalog:product_list') == '/products/'


def test_english_home_page_renders_in_english(client: Client) -> None:
    response = client.get('/')

    assert response.status_code == 200
    body = response.content.decode()
    assert '<html lang="en">' in body
    assert 'Featured products' in body
    assert 'All rights reserved' in body


def test_ukrainian_home_page_renders_translated_strings(client: Client) -> None:
    response = client.get(f'{UK_PREFIX}/')

    assert response.status_code == 200
    body = response.content.decode()
    assert '<html lang="uk">' in body
    assert 'Продукти' in body
    assert 'Увійти' in body


def test_switcher_offers_both_languages_from_ukrainian_page(client: Client) -> None:
    body = client.get(f'{UK_PREFIX}/products/?category=malts').content.decode()

    assert 'href="/products/?category=malts" hreflang="en"' in body
    assert 'href="/uk/products/?category=malts" hreflang="uk"' in body
    assert 'hreflang="uk" lang="uk" class="header__lang-switch-link is-active"' in body


def test_switcher_marks_english_active_on_english_page(client: Client) -> None:
    body = client.get('/products/').content.decode()

    assert 'hreflang="en" lang="en" class="header__lang-switch-link is-active"' in body
    assert 'href="/uk/products/" hreflang="uk"' in body


def test_switcher_drops_prefix_for_english_from_ukrainian_page(client: Client) -> None:
    body = client.get(f'{UK_PREFIX}/').content.decode()

    assert 'href="/" hreflang="en"' in body


def test_ukrainian_product_list_translates_static_text(client: Client) -> None:
    body = client.get(f'{UK_PREFIX}/products/').content.decode()

    assert 'Застосувати фільтри' in body
    assert 'Усі категорії' in body


def test_technical_endpoints_stay_outside_language_prefix(client: Client) -> None:
    assert client.get('/health/').status_code == 200
    assert client.get('/api/products/').status_code == 200


def test_technical_endpoints_are_not_available_under_ukrainian_prefix(client: Client) -> None:
    assert client.get(f'{UK_PREFIX}/health/').status_code == 404
    assert client.get(f'{UK_PREFIX}/api/products/').status_code == 404


def test_login_redirect_keeps_language_prefix(client: Client) -> None:
    response = client.get(f'{UK_PREFIX}/orders/')

    assert response.status_code == 302
    assert response.headers['Location'] == f'{UK_PREFIX}/login/?next={UK_PREFIX}/orders/'


def test_redirects_stay_inside_current_language(client: Client) -> None:
    product = make_product()

    response = client.post(f'{UK_PREFIX}/cart/add/{product.pk}/', {'quantity': 1})

    assert response.status_code == 302
    assert response.headers['Location'] == product.get_absolute_url()
    assert response.headers['Location'].startswith(UK_PREFIX)


def test_model_choices_are_translated() -> None:
    order = _order()

    with translation.override('uk'):
        assert Order.Status(order.status).label == 'Очікує'
        assert Order.PaymentMethod(order.payment_method).label == 'Картка'


def test_out_of_stock_error_is_translated() -> None:
    with translation.override('uk'):
        message = str(OutOfStockError('Citra', 5, 2))

    assert message == 'У наявності лише 2 шт. «Citra» (замовлено 5 шт.).'


def test_cancel_error_is_translated() -> None:
    order = _order(Order.Status.SHIPPED)

    with translation.override('uk'), pytest.raises(OrderTransitionError) as excinfo:
        cancel_order(order)

    assert 'не можна скасувати' in str(excinfo.value)
