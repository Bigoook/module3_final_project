from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.catalog.models import Category, Product
from apps.reviews.models import Review


def _make_category(name: str = 'Shop', slug: str = 'shop') -> Category:
    return Category.objects.create(name=name, slug=slug)


def _make_product(name: str, category: Category, **kwargs):
    return Product.objects.create(
        name=name,
        slug=name.replace(' ', '-').lower(),
        description='description',
        price=Decimal('9.99'),
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
