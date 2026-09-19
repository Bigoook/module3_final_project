import pytest
from django.core.management import call_command

from apps.catalog.models import Category, Product
from apps.reviews.models import Review


@pytest.mark.django_db
def test_seed_data_creates_demo_content(settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path

    call_command('seed_data')

    assert Category.objects.count() == 7
    assert Product.objects.count() == 15
    assert Product.objects.filter(image='').count() == 3
    assert Review.objects.count() == 6


@pytest.mark.django_db
def test_seed_data_is_idempotent(settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path

    call_command('seed_data')
    first_products = Product.objects.count()

    call_command('seed_data')

    assert Product.objects.count() == first_products
