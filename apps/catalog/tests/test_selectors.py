from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.catalog.models import Category, Product
from apps.catalog.selectors import (
    get_featured_products,
    get_product_detail,
    get_product_detail_by_slug,
    get_product_listing,
    get_related_products,
)
from apps.reviews.models import Review


def _make_products(*names: str) -> tuple[Category, list[Product]]:
    category = Category.objects.create(name='Shop', slug='shop')
    products = [
        Product.objects.create(
            name=name,
            slug=name.replace(' ', '-'),
            description='',
            price=Decimal('9.99'),
            category=category,
        )
        for name in names
    ]
    return category, products


@pytest.mark.django_db
def test_featured_orders_by_rating_then_newest_and_limits() -> None:
    _, products = _make_products('Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta')
    user = get_user_model().objects.create_user(username='reviewer')

    Review.objects.create(product=products[2], user=user, rating=5, comment='top')
    Review.objects.create(product=products[0], user=user, rating=3, comment='mid')

    featured = list(get_featured_products(limit=3))

    assert featured[0].pk == products[2].pk
    assert len(featured) == 3


@pytest.mark.django_db
def test_featured_excludes_inactive_products() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    Product.objects.create(
        name='Active',
        slug='active',
        description='',
        price=Decimal('9.99'),
        category=category,
    )
    Product.objects.create(
        name='Hidden',
        slug='hidden',
        description='',
        price=Decimal('9.99'),
        category=category,
        is_active=False,
    )

    assert {p.slug for p in get_featured_products()} == {'active'}


@pytest.mark.django_db
def test_listing_filters_by_category_and_orders() -> None:
    malts = Category.objects.create(name='Malts', slug='malts')
    hops = Category.objects.create(name='Hops', slug='hops')
    first = Product.objects.create(
        name='A',
        slug='a',
        description='',
        price=Decimal('1.00'),
        category=malts,
    )
    Product.objects.create(
        name='B',
        slug='b',
        description='',
        price=Decimal('2.00'),
        category=hops,
    )

    listed = list(get_product_listing(category_slug='malts'))

    assert listed == [first]


@pytest.mark.django_db
def test_listing_applies_ordering() -> None:
    _, products = _make_products('B', 'A')

    listed = list(get_product_listing(ordering='name'))

    assert listed == [products[1], products[0]]


@pytest.mark.django_db
def test_listing_orders_by_rating_annotation() -> None:
    _, products = _make_products('Alpha', 'Beta')
    user = get_user_model().objects.create_user(username='reviewer')

    Review.objects.create(product=products[0], user=user, rating=5, comment='top')
    Review.objects.create(
        product=products[1],
        user=get_user_model().objects.create_user(username='reviewer2'),
        rating=1,
        comment='bad',
    )
    Review.objects.create(
        product=products[1],
        user=get_user_model().objects.create_user(username='reviewer3'),
        rating=5,
        comment='ok',
    )

    listed = list(get_product_listing(ordering='-rating'))

    assert listed[0].pk == products[0].pk


@pytest.mark.django_db
def test_listing_ignores_unknown_ordering() -> None:
    _, products = _make_products('Alpha', 'Beta')

    listed = list(get_product_listing(ordering='rating; DROP TABLE product'))

    assert set(listed) == set(products)


@pytest.mark.django_db
def test_listing_excludes_inactive() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    Product.objects.create(
        name='Hidden',
        slug='hidden',
        description='',
        price=Decimal('9.99'),
        category=category,
        is_active=False,
    )

    assert list(get_product_listing()) == []


@pytest.mark.django_db
def test_product_detail_by_pk_and_slug() -> None:
    _, products = _make_products('Alpha')
    user = get_user_model().objects.create_user(username='reviewer')
    review = Review.objects.create(
        product=products[0], user=user, rating=5, comment='top'
    )

    detail = get_product_detail(products[0].pk)
    by_slug = get_product_detail_by_slug(products[0].slug)

    assert detail is not None
    assert by_slug is not None
    assert detail.pk == products[0].pk
    assert list(detail.reviews.all()) == [review]


@pytest.mark.django_db
def test_product_detail_missing_and_inactive_return_none() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    Product.objects.create(
        name='Hidden',
        slug='hidden',
        description='',
        price=Decimal('9.99'),
        category=category,
        is_active=False,
    )

    assert get_product_detail(999) is None
    assert get_product_detail_by_slug('hidden') is None


@pytest.mark.django_db
def test_related_products_exclude_self_and_other_categories() -> None:
    malts = Category.objects.create(name='Malts', slug='malts')
    hops = Category.objects.create(name='Hops', slug='hops')
    same = Product.objects.create(
        name='Same',
        slug='same',
        description='',
        price=Decimal('1.00'),
        category=malts,
    )
    other = Product.objects.create(
        name='Other',
        slug='other',
        description='',
        price=Decimal('1.00'),
        category=hops,
    )
    target = Product.objects.create(
        name='Target',
        slug='target',
        description='',
        price=Decimal('1.00'),
        category=malts,
    )

    related = list(get_related_products(target))

    assert same.pk in [p.pk for p in related]
    assert other.pk not in [p.pk for p in related]
