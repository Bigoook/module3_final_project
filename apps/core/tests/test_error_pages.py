from django.template.loader import get_template
from django.test import override_settings
from django.utils import translation


@override_settings(SHOP_NAME='Test Brewery')
def test_500_template_takes_shop_name_from_settings() -> None:
    html = get_template('500.html').render()

    assert '<title>Server error | Test Brewery</title>' in html
    assert '<p class="logo-text">Test Brewery</p>' in html
    assert 'alt="Test Brewery Logo"' in html
    assert '<p class="footer__copyright">Test Brewery.' in html


def test_500_template_renders_without_request_context() -> None:
    html = get_template('500.html').render()

    assert '<html lang="en">' in html
    assert 'Something went wrong' in html


def test_500_template_follows_active_language() -> None:
    with translation.override('uk'):
        html = get_template('500.html').render()

    assert '<html lang="uk">' in html
    assert 'Щось пішло не так' in html
