from decimal import Decimal

from django.test import override_settings

from apps.core.templatetags.shop_tags import money, stars


@override_settings(SHOP_CURRENCY='USD')
def test_money_uses_configured_currency_symbol() -> None:
    assert money(Decimal('12.50')) == '$12.50'


@override_settings(SHOP_CURRENCY='USD')
def test_money_rounds_to_two_decimals() -> None:
    assert money(Decimal('9.999')) == '$10.00'


def test_stars_renders_expected_icon_count() -> None:
    html = stars(4.5)

    assert html.count('<i class="fa-solid fa-star"></i>') == 4
    assert html.count('fa-star-half-stroke') == 1
    assert html.count('fa-regular fa-star') == 0
