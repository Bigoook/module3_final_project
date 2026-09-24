from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.reviews.models import Review


@pytest.mark.django_db
def test_category_str_and_default_parent() -> None:
    category = Category.objects.create(name='Electronics', slug='electronics')

    assert category.parent is None
    assert str(category) == 'Electronics'


@pytest.mark.django_db
def test_category_hierarchy_links_parent_and_children() -> None:
    parent = Category.objects.create(name='Electronics', slug='electronics')
    child = Category.objects.create(name='Phones', slug='phones', parent=parent)

    assert child.parent == parent
    assert list(parent.children.all()) == [child]


@pytest.mark.django_db
def test_category_slug_must_be_unique() -> None:
    Category.objects.create(name='Electronics', slug='shop')

    with pytest.raises(IntegrityError):
        Category.objects.create(name='Gadgets', slug='shop')


@pytest.mark.django_db
def test_product_stores_decimal_price_and_positive_stock() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='Good sound',
        price=Decimal('99.99'),
        category=category,
        stock=7,
    )

    assert product.price == Decimal('99.99')
    assert product.stock == 7
    assert product.is_active is True
    assert str(product) == 'Headphones'


@pytest.mark.django_db
def test_product_price_validator_rejects_zero() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('0'),
        category=category,
    )

    with pytest.raises(ValidationError):
        product.full_clean()


@pytest.mark.django_db
def test_product_negative_price_enforced_at_db_level() -> None:
    category = Category.objects.create(name='Shop', slug='shop')

    with pytest.raises(IntegrityError):
        Product.objects.create(
            name='Headphones',
            slug='headphones',
            description='',
            price=Decimal('-1.00'),
            category=category,
        )


@pytest.mark.django_db
def test_category_with_products_cannot_be_deleted() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('9.99'),
        category=category,
    )

    with pytest.raises(ProtectedError):
        category.delete()


@pytest.mark.django_db
def test_category_absolute_url_points_to_category_listing() -> None:
    category = Category.objects.create(name='Malts', slug='malts')

    assert category.get_absolute_url() == reverse('catalog:product_list', kwargs={'category_slug': 'malts'})


@pytest.mark.django_db
def test_product_absolute_url_and_in_stock() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('9.99'),
        category=category,
        stock=0,
    )

    assert product.get_absolute_url() == reverse('catalog:product_detail', kwargs={'slug': 'headphones'})
    assert product.in_stock is False

    product.stock = 1
    assert product.in_stock is True


@pytest.mark.django_db
def test_slug_auto_generated_for_english_name() -> None:
    category = Category.objects.create(name='Shop')
    product = Product.objects.create(
        name='Citra Hops 50g',
        description='',
        price=Decimal('9.99'),
        category=category,
    )

    assert category.slug == 'shop'
    assert product.slug == 'citra-hops-50g'


@pytest.mark.django_db
def test_slug_transliterated_from_ukrainian_name() -> None:
    category = Category.objects.create(name='Хміль')
    product = Product.objects.create(
        name='Хміль Карамельний',
        description='',
        price=Decimal('9.99'),
        category=category,
    )

    assert category.slug == 'khmil'
    assert product.slug.startswith('khmil')


@pytest.mark.django_db
def test_slug_kept_when_provided_explicitly() -> None:
    product = Product.objects.create(
        name='Citra Hops',
        slug='custom-slug',
        description='',
        price=Decimal('9.99'),
        category=Category.objects.create(name='Shop'),
    )

    assert product.slug == 'custom-slug'


@pytest.mark.django_db
def test_for_listing_annotates_rating_averages() -> None:
    from django.contrib.auth import get_user_model

    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('9.99'),
        category=category,
        stock=7,
    )
    user = get_user_model().objects.create_user(username='reviewer')

    Review.objects.create(product=product, user=user, rating=4, comment='Nice')
    Review.objects.create(
        product=product,
        user=get_user_model().objects.create_user(username='reviewer2'),
        rating=5,
        comment='Great',
    )

    listed = Product.objects.for_listing().get(pk=product.pk)
    reloaded = Product.objects.for_listing().get(pk=product.pk)

    assert listed.rating_avg == pytest.approx(4.5)
    assert listed.rating_count == 2
    assert reloaded.rating_avg == pytest.approx(4.5)
    assert reloaded.rating_count == 2


@pytest.mark.django_db
def test_for_listing_excludes_inactive_products() -> None:

    category = Category.objects.create(name='Shop', slug='shop')
    active = Product.objects.create(
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

    assert list(Product.objects.for_listing()) == [active]


@pytest.mark.django_db
def test_for_listing_defaults_ratings_to_zero() -> None:
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price=Decimal('9.99'),
        category=category,
    )

    listed = Product.objects.for_listing().get(pk=product.pk)

    assert listed.rating_avg == pytest.approx(0.0)
    assert listed.rating_count == 0
    assert product.rating_avg == pytest.approx(0.0)
    assert product.rating_count == 0
