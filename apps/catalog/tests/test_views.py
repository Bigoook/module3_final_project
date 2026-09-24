from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.catalog.models import Category, Product
from apps.orders.models import Order, OrderItem
from apps.reviews.models import Review


def _make_category(name: str = 'Shop', slug: str = 'shop') -> Category:
    return Category.objects.create(name=name, slug=slug)


def _make_product(name: str, category: Category, **kwargs):
    price = kwargs.pop('price', Decimal('9.99'))
    return Product.objects.create(
        name=name,
        slug=name.replace(' ', '-').lower(),
        description='description',
        price=price,
        category=category,
        **kwargs,
    )


@pytest.mark.django_db
def test_home_renders_featured_products() -> None:
    category = _make_category()
    product = _make_product('Citra Hops', category)

    response = Client().get('/')

    assert response.status_code == 200
    assert product.name.encode() in response.content


@pytest.mark.django_db
def test_home_header_lists_child_categories() -> None:
    parent = _make_category('Malts', 'malts')
    Category.objects.create(name='Base Malts', slug='base-malts', parent=parent)

    response = Client().get('/')

    assert response.status_code == 200
    assert b'Malts' in response.content
    assert b'Base Malts' in response.content


@pytest.mark.django_db
def test_product_list_renders_products_with_pagination_context() -> None:
    category = _make_category()
    for index in range(13):
        _make_product(f'Hops {index}', category)

    response = Client().get('/products/')

    assert response.status_code == 200
    assert response.context['is_paginated'] is True
    assert len(response.context['products']) == 12
    assert response.context['paginator'].count == 13


@pytest.mark.django_db
def test_product_list_respects_ordering_and_category() -> None:
    malts = _make_category('Malts', 'malts')
    hops = _make_category('Hops', 'hops')
    a_malt = _make_product('A Malt', malts)
    b_malt = _make_product('B Malt', malts)
    hop = _make_product('Hop', hops)

    response = Client().get('/products/?ordering=name')

    assert response.status_code == 200
    assert list(response.context['products']) == [a_malt, b_malt, hop]

    category_response = Client().get('/category/malts/')

    assert category_response.status_code == 200
    assert len(category_response.context['products']) == 2


@pytest.mark.django_db
def test_product_list_filters_via_sidebar_params() -> None:
    malts = _make_category('Malts', 'malts')
    _make_product('Citra Hops', _make_category('Hops', 'hops'))
    _make_product('A Malt', malts, price=Decimal('1.00'), stock=0)
    _make_product('B Malt', malts, price=Decimal('15.00'), stock=5)

    filtered = Client().get('/products/?category=malts&search=malt&min_price=10&in_stock=true')

    assert filtered.status_code == 200
    assert [p.slug for p in filtered.context['products']] == ['b-malt']
    assert [p.slug for p in filtered.context['filter'].qs] == ['b-malt']


@pytest.mark.django_db
def test_product_detail_renders_active_product_and_404s_otherwise() -> None:
    category = _make_category()
    product = _make_product('Citra Hops', category)
    inactive = _make_product('Hidden', category, is_active=False)

    response = Client().get(f'/products/{product.slug}/')
    hidden = Client().get(f'/products/{inactive.slug}/')
    missing = Client().get('/products/unknown/')

    assert response.status_code == 200
    assert product.name.encode() in response.content
    assert hidden.status_code == 404
    assert missing.status_code == 404


@pytest.mark.django_db
def test_product_detail_preloads_reviews() -> None:
    category = _make_category()
    product = _make_product('Citra Hops', category)
    user = get_user_model().objects.create_user(username='reviewer')
    Review.objects.create(product=product, user=user, rating=5, comment='Great')

    response = Client().get(f'/products/{product.slug}/')

    assert response.status_code == 200
    assert b'Great' in response.content


@pytest.mark.django_db
def test_product_detail_includes_related_products() -> None:
    category = _make_category()
    product = _make_product('Target', category)
    related = _make_product('Related', category)
    _make_product('Far', _make_category('Hops', 'hops'))

    response = Client().get(f'/products/{product.slug}/')

    assert response.status_code == 200
    related_slugs = [p.slug for p in response.context['related_products']]
    assert related_slugs == [related.slug]


def _make_purchased_order(user, product) -> Order:
    order = Order.objects.create(user=user, total_price=Decimal('1.00'))
    OrderItem.objects.create(order=order, product=product, quantity=1, price=Decimal('1.00'))
    return order


@pytest.mark.django_db
def test_product_detail_can_review_states() -> None:
    category = _make_category()
    product = _make_product('Citra Hops', category)
    user = get_user_model().objects.create_user(username='buyer', password='pass12345')
    client = Client()
    url = f'/products/{product.slug}/'

    assert client.get(url).context['can_review'] is False

    client.force_login(user)
    assert client.get(url).context['can_review'] is False

    _make_purchased_order(user, product)
    assert client.get(url).context['can_review'] is True

    Review.objects.create(product=product, user=user, rating=4, comment='done')
    assert client.get(url).context['can_review'] is False


@pytest.mark.django_db
def test_product_detail_renders_review_and_cart_forms() -> None:
    category = _make_category()
    product = _make_product('Citra Hops', category, stock=5)
    user = get_user_model().objects.create_user(username='buyer', password='pass12345')
    _make_purchased_order(user, product)

    client = Client()
    client.force_login(user)
    response = client.get(f'/products/{product.slug}/')

    assert response.status_code == 200
    assert b'name="rating"' in response.content
    assert b'name="comment"' in response.content
    assert b'name="quantity"' in response.content
    assert b'Submit review' in response.content
