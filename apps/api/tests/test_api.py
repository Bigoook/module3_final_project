from decimal import Decimal

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.factories import make_product

PASSWORD = 'Mega-Secret-2026!'


@pytest.fixture
def throttle_rates(monkeypatch: pytest.MonkeyPatch):
    """Override DRF rate limits for one test.

    `override_settings` does not work here: SimpleRateThrottle binds
    THROTTLE_RATES as a class attribute at import time (rest_framework/throttling.py),
    so the rates are frozen before any test runs.
    """

    def _apply(**rates: str) -> None:
        merged = {**settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], **rates}
        monkeypatch.setattr(SimpleRateThrottle, 'THROTTLE_RATES', merged)

    return _apply


def _register(client: APIClient, username: str = 'alice') -> int:
    response = client.post(
        reverse('api:user_register'),
        {'username': username, 'email': f'{username}@example.com', 'password': PASSWORD},
        format='json',
    )
    assert response.status_code == 201
    return response.data['id']


def _login(client: APIClient, username: str = 'alice') -> None:
    response = client.post(
        reverse('api:user_login'),
        {'username': username, 'password': PASSWORD},
        format='json',
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')


@pytest.mark.django_db
def test_schema_and_docs_are_available() -> None:
    make_product(name='Pale malt', price='10.00', stock=5)

    client = APIClient()

    schema = client.get('/api/schema/')
    assert schema.status_code == 200
    assert schema.data['info']['title'] == f'{settings.SHOP_NAME} API'

    paths = schema.data['paths']
    assert '/api/products/' in paths
    assert '/api/products/{id}/' in paths
    assert '/api/cart/' in paths
    assert '/api/orders/' in paths
    assert '/api/users/register/' in paths
    assert '/api/users/login/' in paths
    assert '/api/productss/' not in paths

    docs = client.get('/api/docs/')
    assert docs.status_code == 200
    assert 'swagger-ui' in docs.content.decode()


@pytest.mark.django_db
def test_products_list_is_paginated_and_filtered() -> None:
    make_product(name='Centennial hops', price='3.00', stock=4)
    make_product(name='Cascade hops', price='2.50', stock=0)
    make_product(name='Pale malt', price='1.50', stock=9)
    make_product(name='Hidden', is_active=False)

    client = APIClient()
    response = client.get('/api/products/')

    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 3
    first = response.data['results'][0]
    assert set(first) >= {'id', 'name', 'slug', 'price', 'rating_avg', 'rating_count', 'in_stock'}

    searched = client.get('/api/products/?search=hops').data['results']
    assert {item['name'] for item in searched} == {'Centennial hops', 'Cascade hops'}

    in_stock = client.get('/api/products/?in_stock=true').data['results']
    assert {item['name'] for item in in_stock} == {'Centennial hops', 'Pale malt'}

    priced = client.get('/api/products/?min_price=2&max_price=3').data['results']
    assert {item['name'] for item in priced} == {'Centennial hops', 'Cascade hops'}

    by_name = client.get('/api/products/?ordering=name').data['results']
    assert [item['name'] for item in by_name] == ['Cascade hops', 'Centennial hops', 'Pale malt']


@pytest.mark.django_db
def test_product_detail_with_reviews_and_related() -> None:
    product = make_product(name='Pale malt')
    other = make_product(name='Pilsner malt', category=product.category)

    client = APIClient()
    response = client.get(f'/api/products/{product.pk}/')

    assert response.status_code == 200
    body = response.data
    assert body['name'] == 'Pale malt'
    assert body['reviews'] == []
    assert body['can_review'] is False
    assert [item['id'] for item in body['related_products']] == [other.pk]

    assert client.get('/api/products/99999/').status_code == 404

    make_product(name='Hidden', is_active=False)
    hidden = make_product(name='Also hidden', is_active=False)
    assert client.get(f'/api/products/{hidden.pk}/').status_code == 404


@pytest.mark.django_db
def test_register_login_cycle_and_validation() -> None:
    client = APIClient()
    user_id = _register(client)

    assert (
        client.post(
            reverse('api:user_register'),
            {'username': 'bob', 'email': 'alice@example.com', 'password': PASSWORD},
            format='json',
        ).status_code
        == 400
    )

    assert (
        client.post(
            reverse('api:user_register'),
            {'username': 'weak', 'email': 'weak@example.com', 'password': '1234'},
            format='json',
        ).status_code
        == 400
    )

    logged = APIClient()
    response = logged.post(
        reverse('api:user_login'),
        {'username': 'alice', 'password': PASSWORD},
        format='json',
    )
    assert response.status_code == 200
    assert 'access' in response.data and 'refresh' in response.data

    assert (
        logged.post(
            reverse('api:user_login'),
            {'username': 'alice', 'password': 'wrong'},
            format='json',
        ).status_code
        == 401
    )

    assert (
        client.post(
            reverse('api:user_register'),
            {'username': 'alice', 'email': 'new@example.com', 'password': PASSWORD},
            format='json',
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_cart_add_update_remove_and_guards() -> None:
    product = make_product(name='Pale malt', price='10.00', stock=5)
    client = APIClient()
    _register(client)
    _login(client)

    added = client.post('/api/cart/', {'product_id': product.pk, 'quantity': 2}, format='json')
    assert added.status_code == 201
    assert added.data == {'status': 'added', 'quantity': 2}

    view = client.get('/api/cart/')
    assert view.status_code == 200
    assert view.data['is_empty'] is False
    assert view.data['total'] == '20.00'
    assert view.data['lines'][0]['quantity'] == 2

    updated = client.patch('/api/cart/', {'product_id': product.pk, 'quantity': 1}, format='json')
    assert updated.data == {'status': 'updated', 'quantity': 1}

    capped = client.patch('/api/cart/', {'product_id': product.pk, 'quantity': 99}, format='json')
    assert capped.data == {'status': 'capped', 'quantity': 5}

    removed = client.delete(f'/api/cart/?product_id={product.pk}')
    assert removed.status_code == 204
    assert client.get('/api/cart/').data['is_empty'] is True

    out_of_stock = make_product(name='Empty stock', stock=0)
    blocked = client.post('/api/cart/', {'product_id': out_of_stock.pk, 'quantity': 1}, format='json')
    assert blocked.status_code == 400

    assert client.post('/api/cart/', {'product_id': 777777, 'quantity': 1}, format='json').status_code == 404

    guest = APIClient()
    assert guest.get('/api/cart/').status_code == 401
    assert guest.post('/api/cart/', {'product_id': product.pk}, format='json').status_code == 401


@pytest.mark.django_db
def test_order_create_list_detail_cancel() -> None:
    product = make_product(name='Pale malt', price='10.00', stock=5)
    client = APIClient()
    _register(client)
    _login(client)

    client.post('/api/cart/', {'product_id': product.pk, 'quantity': 2}, format='json')

    created = client.post('/api/orders/', {}, format='json')
    assert created.status_code == 201
    order = created.data
    assert order['status'] == 'pending'
    assert order['total_price'] == Decimal('20.00')
    assert order['items'][0]['product_name'] == 'Pale malt'
    assert client.get('/api/cart/').data['is_empty'] is True

    product.refresh_from_db()
    assert product.stock == 3

    listing = client.get('/api/orders/')
    assert listing.status_code == 200
    assert listing.data['count'] == 1
    assert listing.data['results'][0]['id'] == order['id']

    other = APIClient()
    _register(other, username='bob')
    _login(other, username='bob')
    assert other.get(f'/api/orders/{order["id"]}/').status_code == 404

    detail = client.get(f'/api/orders/{order["id"]}/')
    assert detail.status_code == 200

    cancelled = client.patch(f'/api/orders/{order["id"]}/', {'status': 'cancelled'}, format='json')
    assert cancelled.status_code == 200
    assert cancelled.data['status'] == 'cancelled'

    forbidden = client.patch(f'/api/orders/{order["id"]}/', {'status': 'paid'}, format='json')
    assert forbidden.status_code == 400

    second = client.post('/api/orders/', {}, format='json')
    assert second.status_code == 400  # empty cart


@pytest.mark.django_db
def test_order_delete_cancels_and_auth_is_required() -> None:
    product = make_product(name='Pale malt', price='10.00', stock=5)
    client = APIClient()
    _register(client)
    _login(client)
    client.post('/api/cart/', {'product_id': product.pk, 'quantity': 1}, format='json')
    order_id = client.post('/api/orders/', {}, format='json').data['id']

    removed = client.delete(f'/api/orders/{order_id}/')
    assert removed.status_code == 204

    detail = client.get(f'/api/orders/{order_id}/')
    assert detail.status_code == 200
    assert detail.data['status'] == 'cancelled'

    guest = APIClient()
    assert guest.get('/api/orders/').status_code == 401
    assert guest.post('/api/orders/', {}, format='json').status_code == 401


@pytest.mark.django_db
def test_review_create_list_and_permission_rules() -> None:
    product = make_product(name='Pale malt', price='10.00', stock=5)
    client = APIClient()
    _register(client)
    _login(client)

    before_any = client.get(f'/api/products/{product.pk}/reviews/')
    assert before_any.status_code == 200
    assert before_any.data == []

    unpaid = client.post(
        f'/api/products/{product.pk}/reviews/',
        {'rating': 5, 'comment': 'Great malt.'},
        format='json',
    )
    assert unpaid.status_code == 400

    client.post('/api/cart/', {'product_id': product.pk, 'quantity': 1}, format='json')
    client.post('/api/orders/', {}, format='json')

    created = client.post(
        f'/api/products/{product.pk}/reviews/',
        {'rating': 5, 'comment': 'Great malt.'},
        format='json',
    )
    assert created.status_code == 201
    assert created.data['rating'] == 5
    assert created.data['user'] == 'alice'

    duplicate = client.post(
        f'/api/products/{product.pk}/reviews/',
        {'rating': 4, 'comment': 'Again.'},
        format='json',
    )
    assert duplicate.status_code == 400

    listed = client.get(f'/api/products/{product.pk}/reviews/')
    assert len(listed.data) == 1

    guest = APIClient()
    assert (
        guest.post(
            f'/api/products/{product.pk}/reviews/',
            {'rating': 5, 'comment': 'Nope.'},
            format='json',
        ).status_code
        == 401
    )
    assert guest.get(f'/api/products/{product.pk}/reviews/').status_code == 200


@pytest.mark.django_db
def test_registration_and_login_are_rate_limited(throttle_rates) -> None:
    throttle_rates(register='2/hour', login='2/min')
    client = APIClient()

    for username in ('alice', 'bob'):
        response = client.post(
            reverse('api:user_register'),
            {'username': username, 'email': f'{username}@example.com', 'password': PASSWORD},
            format='json',
        )
        assert response.status_code == 201

    blocked = client.post(
        reverse('api:user_register'),
        {'username': 'carol', 'email': 'carol@example.com', 'password': PASSWORD},
        format='json',
    )
    assert blocked.status_code == 429
    assert 'Retry-After' in blocked.headers

    logged = APIClient()
    for _ in range(2):
        assert (
            logged.post(
                reverse('api:user_login'),
                {'username': 'alice', 'password': PASSWORD},
                format='json',
            ).status_code
            == 200
        )

    assert (
        logged.post(
            reverse('api:user_login'),
            {'username': 'alice', 'password': 'wrong'},
            format='json',
        ).status_code
        == 429
    )


@pytest.mark.django_db
def test_browsing_endpoints_are_not_rate_limited_by_default() -> None:
    """The default anon/user rates must stay above what a normal session needs."""
    make_product(name='Pale malt', price='10.00', stock=5)
    client = APIClient()

    for _ in range(30):
        assert client.get('/api/products/').status_code == 200
