"""DRF throttles that identify the client by its real IP.

Stock ``AnonRateThrottle`` keys on ``REMOTE_ADDR``. Behind a reverse proxy that
address belongs to the proxy, so every visitor would share a single bucket: one
abusive client could lock all users out of /api/users/login/. These subclasses
resolve the address with ``apps.core.clientip`` instead.
"""

from __future__ import annotations

from typing import Any

from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle

from apps.core.clientip import get_client_ip


class _ClientIpMixin:
    """Key the throttle on the forwarded client IP when the peer is trusted."""

    # Declared for typing only: SimpleRateThrottle sets self.scope from the
    # view's throttle_scope at request time.
    scope: str | None

    def get_ident(self, request: Any) -> str:
        ident = get_client_ip(request) or 'unknown'
        if self.scope:
            return f'{self.scope}_{ident}'
        return ident


class ClientIpAnonRateThrottle(_ClientIpMixin, AnonRateThrottle):
    """AnonRateThrottle keyed by the real client IP."""


class ClientIpScopedRateThrottle(_ClientIpMixin, ScopedRateThrottle):
    """ScopedRateThrottle (login, register) keyed by the real client IP."""
