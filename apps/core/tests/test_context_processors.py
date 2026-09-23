from typing import TYPE_CHECKING, Any, cast

import pytest
from django.conf import settings
from django.test import RequestFactory

from apps.catalog.models import Category
from apps.core.context_processors import main_context
from apps.orders.cart import CART_SESSION_KEY

if TYPE_CHECKING:
    from django.db.models import QuerySet


def _request() -> Any:
    request = RequestFactory().get('/')
    setattr(request, 'session', {})
    return request


@pytest.mark.django_db
def test_main_context_categories_are_top_level_only() -> None:
    parent = Category.objects.create(name='Malts', slug='malts')
    Category.objects.create(name='Base Malts', slug='base-malts', parent=parent)
    Category.objects.create(name='Hops', slug='hops')

    categories = cast('QuerySet[Category]', main_context(_request())['categories'])

    assert {c.slug for c in categories} == {'malts', 'hops'}


def test_main_context_reads_shop_name_from_settings() -> None:
    assert main_context(_request())['SHOP_NAME'] == settings.SHOP_NAME


def test_main_context_reads_cart_count_from_session() -> None:
    request = _request()
    request.session[CART_SESSION_KEY] = {'10': 3, '12': 1}

    assert main_context(request)['cart_count'] == 4


def test_main_context_cart_count_is_zero_for_guest() -> None:
    assert main_context(_request())['cart_count'] == 0
