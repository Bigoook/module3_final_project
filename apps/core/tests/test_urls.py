import pytest
from django.urls import resolve, reverse


@pytest.mark.parametrize(
    ('name', 'kwargs'),
    [
        ('catalog:home', {}),
        ('catalog:product_list', {}),
        ('catalog:product_list', {'category_slug': 'malts'}),
        ('catalog:product_detail', {'slug': 'citra-hops'}),
        ('accounts:login', {}),
        ('accounts:register', {}),
        ('accounts:profile', {}),
        ('accounts:logout', {}),
        ('orders:cart', {}),
        ('orders:cart_add', {'product_id': 1}),
    ],
)
def test_named_urls_resolve_and_reverse(name: str, kwargs: dict[str, str]) -> None:
    url = reverse(name, kwargs=kwargs)
    resolved = resolve(url)

    assert resolved.url_name == name.rsplit(':', maxsplit=1)[-1]
    assert resolved.namespace == name.split(':', maxsplit=1)[0]
