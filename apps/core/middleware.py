"""Rate limiting for the session login and the admin login.

DRF throttles (see config/settings/base.py) only guard ``/api/``. The two
credential forms that matter most are plain Django views, so without this
middleware ``/accounts/login/`` and ``/admin/login/`` would accept an unlimited
number of password guesses. Counts share the same cache as the API throttles, so
all gunicorn workers see one counter.
"""

from __future__ import annotations

from typing import Any, Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from apps.core.clientip import get_client_ip
from apps.core.ratelimit import SlidingWindowLimiter, parse_rate

# Matched on the URL name rather than the full view name ("admin:login"): the
# custom admin site in config/admin_site.py resolves as "shop_admin:login", and
# the storefront login is served under an i18n prefix, so a namespaced match
# would miss both. Any view resolving to the name "login" is throttled, which
# fails safe if another login page is added later.
LOGIN_URL_NAMES = frozenset({'login'})

TOO_MANY_REQUESTS_BODY = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<title>Too many attempts</title></head>'
    '<body><h1>Too many attempts</h1>'
    '<p>Please wait a minute before trying to sign in again.</p>'
    '</body></html>'
)


class LoginThrottleMiddleware:
    """Throttle credential POSTs; pass-through for every other request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.limiter = SlidingWindowLimiter()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., Any],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponse | None:
        # Only the credential-carrying POST; reloading the form must never lock
        # a real user out.
        if request.method != 'POST':
            return None

        match = request.resolver_match
        if match is None or match.url_name not in LOGIN_URL_NAMES:
            return None

        ident = get_client_ip(request)
        if not ident:
            return None

        retry_after = self.limiter.hit(f'login_attempts_{ident}', parse_rate(settings.LOGIN_ATTEMPT_RATE))
        if retry_after is None:
            return None

        response = HttpResponse(TOO_MANY_REQUESTS_BODY, status=429, content_type='text/html; charset=utf-8')
        response['Retry-After'] = str(retry_after)
        return response
