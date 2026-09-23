from typing import TYPE_CHECKING, cast

import pytest
from django.conf import settings

from apps.catalog.models import Category
from apps.core.context_processors import main_context

if TYPE_CHECKING:
    from django.db.models import QuerySet


@pytest.mark.django_db
def test_main_context_categories_are_top_level_only() -> None:
    parent = Category.objects.create(name='Malts', slug='malts')
    Category.objects.create(name='Base Malts', slug='base-malts', parent=parent)
    Category.objects.create(name='Hops', slug='hops')

    categories = cast('QuerySet[Category]', main_context(None)['categories'])

    assert {c.slug for c in categories} == {'malts', 'hops'}


def test_main_context_reads_shop_name_from_settings() -> None:
    assert main_context(None)['SHOP_NAME'] == settings.SHOP_NAME
