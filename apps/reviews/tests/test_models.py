import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.catalog.models import Category, Product
from apps.reviews.models import Review


@pytest.mark.django_db
def test_review_enforces_rating_range_on_clean() -> None:
    user = get_user_model().objects.create(username='reviewer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price='9.99',
        category=category,
    )
    valid = Review.objects.create(product=product, user=user, rating=5, comment='ok')

    assert valid.rating == 5

    invalid = Review(product=product, user=user, rating=6, comment='too much')

    with pytest.raises(ValidationError):
        invalid.full_clean()


@pytest.mark.django_db
def test_review_is_unique_per_product_and_user() -> None:
    user = get_user_model().objects.create(username='reviewer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price='9.99',
        category=category,
    )
    Review.objects.create(product=product, user=user, rating=5, comment='first')

    with pytest.raises(IntegrityError):
        Review.objects.create(product=product, user=user, rating=4, comment='second')


@pytest.mark.django_db
def test_deleting_product_cascades_to_reviews() -> None:
    user = get_user_model().objects.create(username='reviewer')
    category = Category.objects.create(name='Shop', slug='shop')
    product = Product.objects.create(
        name='Headphones',
        slug='headphones',
        description='',
        price='9.99',
        category=category,
    )
    Review.objects.create(product=product, user=user, rating=5, comment='ok')

    product.delete()

    assert Review.objects.filter(product_id=product.pk).count() == 0
