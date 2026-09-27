"""Security controls: client IP resolution, login throttling and the CSP header."""

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse

from apps.core.clientip import get_client_ip
from apps.core.ratelimit import SlidingWindowLimiter, parse_rate

User = get_user_model()


def _request(remote_addr: str = '203.0.113.7', forwarded_for: str | None = None):
    extra: dict[str, Any] = {'REMOTE_ADDR': remote_addr}
    if forwarded_for is not None:
        extra['HTTP_X_FORWARDED_FOR'] = forwarded_for
    return RequestFactory().get('/', **extra)


# --- get_client_ip ----------------------------------------------------------


def test_direct_client_ip_is_used_as_is() -> None:
    assert get_client_ip(_request()) == '203.0.113.7'


def test_forwarded_header_is_ignored_without_a_trusted_proxy() -> None:
    """A direct client could otherwise mint a fresh bucket on every request."""
    request = _request(forwarded_for='1.2.3.4')
    assert get_client_ip(request) == '203.0.113.7'


@override_settings(TRUSTED_PROXY_IPS=['172.18.0.0/16'])
def test_forwarded_header_is_honoured_behind_a_trusted_proxy() -> None:
    request = _request(remote_addr='172.18.0.5', forwarded_for='198.51.100.9')
    assert get_client_ip(request) == '198.51.100.9'


@override_settings(TRUSTED_PROXY_IPS=['172.18.0.0/16'])
def test_rightmost_untrusted_address_wins() -> None:
    """Spoofed entries sit on the left; the proxy appends the truth on the right."""
    request = _request(remote_addr='172.18.0.5', forwarded_for='1.1.1.1, 198.51.100.9, 172.18.0.4')
    assert get_client_ip(request) == '198.51.100.9'


@override_settings(TRUSTED_PROXY_IPS=['172.18.0.0/16'])
def test_proxy_only_forwarded_header_falls_back_to_the_peer() -> None:
    request = _request(remote_addr='172.18.0.5', forwarded_for='172.18.0.4, 172.18.0.5')
    assert get_client_ip(request) == '172.18.0.5'


@override_settings(TRUSTED_PROXY_IPS=['172.18.0.0/16'])
def test_garbage_in_the_header_is_skipped() -> None:
    request = _request(remote_addr='172.18.0.5', forwarded_for='not-an-ip, 198.51.100.9')
    assert get_client_ip(request) == '198.51.100.9'


@override_settings(TRUSTED_PROXY_IPS=['garbage-value'])
def test_malformed_trusted_proxy_entries_are_ignored() -> None:
    assert get_client_ip(_request(forwarded_for='198.51.100.9')) == '203.0.113.7'


def test_unparsable_remote_addr_yields_nothing() -> None:
    assert not get_client_ip(_request(remote_addr='not-an-ip'))


# --- parse_rate -------------------------------------------------------------


@pytest.mark.parametrize(
    ('rate', 'expected'),
    [('10/min', (10, 60)), ('5/s', (5, 1)), ('2/h', (2, 3600)), ('1/d', (1, 86400))],
)
def test_parse_rate_reads_count_and_period(rate: str, expected: tuple[int, int]) -> None:
    parsed = parse_rate(rate)
    assert (parsed.limit, parsed.seconds) == expected


@pytest.mark.parametrize('rate', ['', 'many/min', '10/fortnight', '0/min', '-3/min'])
def test_unusable_rates_fall_back(rate: str) -> None:
    """A typo in the environment must not silently switch a limit off."""
    assert parse_rate(rate).limit < 1


# --- SlidingWindowLimiter ---------------------------------------------------


@pytest.mark.django_db
def test_limiter_blocks_once_the_window_is_full() -> None:
    limiter = SlidingWindowLimiter()
    rate = parse_rate('3/min')

    assert [limiter.hit('k', rate) for _ in range(3)] == [None, None, None]

    retry_after = limiter.hit('k', rate)
    assert retry_after is not None
    assert 1 <= retry_after <= 60


@pytest.mark.django_db
def test_limiter_keys_are_independent() -> None:
    limiter = SlidingWindowLimiter()
    rate = parse_rate('1/min')

    assert limiter.hit('a', rate) is None
    assert limiter.hit('b', rate) is None
    assert limiter.hit('a', rate) is not None


# --- login throttling -------------------------------------------------------


@pytest.mark.django_db
@override_settings(LOGIN_ATTEMPT_RATE='3/min', TRUSTED_PROXY_IPS=[])
def test_storefront_login_is_throttled(client) -> None:
    url = reverse('accounts:login')
    payload = {'username': 'nobody', 'password': 'guess'}

    statuses = [client.post(url, payload).status_code for _ in range(3)]
    assert statuses == [200, 200, 200]  # the form re-renders, credentials are wrong

    blocked = client.post(url, payload)
    assert blocked.status_code == 429
    assert 'Retry-After' in blocked.headers


@pytest.mark.django_db
@override_settings(LOGIN_ATTEMPT_RATE='3/min')
def test_admin_login_is_throttled(client) -> None:
    url = reverse('admin:login')
    payload = {'username': 'admin', 'password': 'guess'}

    for _ in range(3):
        assert client.post(url, payload).status_code == 200

    assert client.post(url, payload).status_code == 429


@pytest.mark.django_db
@override_settings(LOGIN_ATTEMPT_RATE='3/min')
def test_successful_login_still_works(client) -> None:
    User.objects.create_user(username='buyer', password='Real-Password-2026')
    response = client.post(
        reverse('accounts:login'),
        {'username': 'buyer', 'password': 'Real-Password-2026'},
    )
    assert response.status_code == 302


@pytest.mark.django_db
@override_settings(LOGIN_ATTEMPT_RATE='3/min')
def test_getting_the_login_page_is_never_throttled(client) -> None:
    url = reverse('accounts:login')
    assert all(client.get(url).status_code == 200 for _ in range(10))


@pytest.mark.django_db
@override_settings(LOGIN_ATTEMPT_RATE='3/min')
def test_other_post_views_are_not_throttled(client) -> None:
    from apps.factories import make_product

    product = make_product(stock=5)
    url = reverse('orders:cart_add', kwargs={'product_id': product.pk})
    assert all(client.post(url, {'quantity': 1}).status_code == 302 for _ in range(5))


# --- Content-Security-Policy ------------------------------------------------


@pytest.mark.django_db
def test_storefront_pages_send_a_strict_csp(client) -> None:
    response = client.get(reverse('catalog:home'))
    csp = response.headers['Content-Security-Policy']

    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert 'https://fonts.googleapis.com' in csp
    assert 'https://cdnjs.cloudflare.com' in csp
    # script-src must not be weakened back to unsafe-inline.
    assert "script-src 'self' 'unsafe-inline'" not in csp
    assert "'unsafe-inline'" not in csp.split('style-src')[0]


@pytest.mark.django_db
def test_admin_is_excluded_from_the_csp(client) -> None:
    User.objects.create_superuser(username='root', password='Admin-Password-2026', email='root@example.com')
    client.login(username='root', password='Admin-Password-2026')

    response = client.get(reverse('shop_admin:index'))
    assert response.status_code == 200
    assert 'Content-Security-Policy' not in response.headers
