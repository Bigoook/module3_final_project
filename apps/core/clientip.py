"""Resolve the real client IP when the app sits behind a reverse proxy.

``REMOTE_ADDR`` is the address of whoever opened the TCP connection, so behind
nginx/Heroku-style ingress every visitor looks like the proxy. Rate limiting keys
on the client IP, so the proxy address has to be unwrapped first.
"""

from __future__ import annotations

import ipaddress
from typing import Any

from django.conf import settings

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network


def _parse_address(value: str) -> IPAddress | None:
    """Return the parsed address, or None for anything malformed."""
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def _parse_networks() -> tuple[IPNetwork, ...]:
    """Parse TRUSTED_PROXY_IPS once per call; the list is tiny and rarely changes."""
    networks = []
    for entry in getattr(settings, 'TRUSTED_PROXY_IPS', []):
        try:
            networks.append(ipaddress.ip_network(entry.strip(), strict=False))
        except ValueError:
            continue
    return tuple(networks)


def _is_trusted(address: IPAddress, networks: tuple[IPNetwork, ...]) -> bool:
    return any(address in network for network in networks)


def get_client_ip(request: Any) -> str:
    """Return the client IP, or an empty string when it cannot be determined.

    X-Forwarded-For is only read when the immediate peer is a trusted proxy.
    Trusting it unconditionally would let any client mint a fresh rate-limit
    bucket per request by sending its own header.
    """
    peer = _parse_address(request.META.get('REMOTE_ADDR', ''))
    if peer is None:
        return ''

    networks = _parse_networks()
    if not _is_trusted(peer, networks):
        return str(peer)

    # The header is "client, proxy1, proxy2, ..." appended left to right, so the
    # right-most address that is not a trusted proxy is the one we want.
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    for candidate in reversed(forwarded.split(',')):
        address = _parse_address(candidate)
        if address is not None and not _is_trusted(address, networks):
            return str(address)

    # Header missing or made only of proxy addresses: the peer is the best we have.
    return str(peer)
