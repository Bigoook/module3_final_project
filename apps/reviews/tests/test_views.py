from decimal import Decimal

import pytest
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.orders.services import create_order
from apps.reviews.models import Review


def _make_product() -> Product:
    category = Category.objects.create(name='Shop', slug='shop')
    return Product.objects.create(
        name='Alpha',
        slug='alpha',
        description='A test product.',
        price=Decimal('12.50'),
        category=category,
    )


def _product_url(product: Product) -> str:
    return reverse('catalog:product_detail', kwargs={'slug': product.slug})


def _review_url(product: Product) -> str:
    return reverse('reviews:create', kwargs={'slug': product.slug})


@pytest.mark.django_db
def test_guest_is_redirected_to_login(client) -> None:
    product = _make_product()

    response = client.get(_review_url(product), follow=True)

    assert response.status_code == 200
    assert response.redirect_chain
    assert reverse('accounts:login') in response.redirect_chain[0][0]


@pytest.mark.django_db
def test_review_requires_a_purchase(client) -> None:
    product = _make_product()
    user = get_user_model().objects.create_user(username='buyer')
    client.force_login(user)

    response = client.post(_review_url(product), {'rating': 5, 'comment': 'Nice!'})

    assert response.status_code == 302
    assert response.url == _product_url(product)
    assert Review.objects.filter(product=product, user=user).count() == 0
    assert any(
        m.level == messages.ERROR for m in messages.get_messages(response.wsgi_request)
    )


@pytest.mark.django_db
def test_purchased_user_can_submit_review(client) -> None:
    product = _make_product()
    user = get_user_model().objects.create_user(username='buyer')
    create_order(user=user, items=[(product, 1)])
    client.force_login(user)

    response = client.post(_review_url(product), {'rating': 4, 'comment': 'Great!'})

    assert response.status_code == 302
    assert response.url == _product_url(product)
    review = Review.objects.get(product=product, user=user)
    assert review.rating == 4
    assert review.comment == 'Great!'
    assert any(m.level == messages.SUCCESS for m in messages.get_messages(response.wsgi_request))


@pytest.mark.django_db
def test_user_cannot_review_same_product_twice(client) -> None:
    product = _make_product()
    user = get_user_model().objects.create_user(username='buyer')
    create_order(user=user, items=[(product, 1)])
    Review.objects.create(product=product, user=user, rating=5, comment='First')
    client.force_login(user)

    response = client.post(_review_url(product), {'rating': 1, 'comment': 'Second'})

    assert Review.objects.filter(product=product, user=user).count() == 1


@pytest.mark.django_db
def test_invalid_review_form_is_rerendered_with_errors(client) -> None:
    product = _make_product()
    user = get_user_model().objects.create_user(username='buyer')
    create_order(user=user, items=[(product, 1)])
    client.force_login(user)

    response = client.post(_review_url(product), {'comment': 'No rating given'})

    assert response.status_code == 200
    assert 'This field is required' in response.content.decode()
    assert Review.objects.filter(product=product, user=user).count() == 0
