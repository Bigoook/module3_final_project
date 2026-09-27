"""A minimal sliding-window rate limiter for plain Django views.

DRF throttles only guard the API. The storefront and admin login forms are
ordinary Django views, so this helper is what keeps password guessing bounded
there. It deliberately mirrors ``rest_framework.throttling.SimpleRateThrottle``:
a list of hit timestamps per key, trimmed to the window on every request.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any

from django.core.cache import caches

PERIOD_SECONDS = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}


@dataclass(frozen=True)
class Rate:
    """A parsed ``10/min`` style limit."""

    limit: int
    seconds: int

    @property
    def cache_timeout(self) -> int:
        return self.seconds


def parse_rate(rate: str, *, default: Rate | None = None) -> Rate:
    """Parse ``<count>/<period>`` where the period is its first letter.

    ``10/min``, ``10/m`` and ``10/minutes`` all mean ten hits per minute, which
    is how DRF's own throttle rates are written. Unusable input falls back to
    ``default`` (or an unlimited rate), so a typo in the environment cannot turn
    a login limit off silently.
    """
    fallback = default or Rate(limit=0, seconds=1)
    count, _, period = rate.partition('/')
    try:
        limit = int(count)
    except ValueError:
        return fallback
    multiplier = PERIOD_SECONDS.get(period.strip()[:1].lower())
    if limit < 1 or multiplier is None:
        return fallback
    return Rate(limit=limit, seconds=multiplier)


class SlidingWindowLimiter:
    """Allow ``rate.limit`` hits per key per ``rate.seconds``."""

    def __init__(self, cache_alias: str = 'default') -> None:
        self._cache_alias = cache_alias

    @property
    def _cache(self) -> Any:
        # Resolved per hit: override_settings(CACHES=...) in tests swaps it out.
        return caches[self._cache_alias]

    def hit(self, key: str, rate: Rate) -> int | None:
        """Record a hit for ``key``.

        Returns None when the request is allowed, otherwise the number of
        seconds until the next attempt would pass.
        """
        if rate.limit < 1:
            return None

        cache = self._cache
        now = time.time()
        window_start = now - rate.seconds
        history = [stamp for stamp in cache.get(key) or [] if stamp > window_start]

        if len(history) >= rate.limit:
            cache.set(key, history, rate.cache_timeout)
            # Retry-After is what a well-behaved client will wait, so round up
            # and never promise more than one full window.
            return max(1, min(rate.seconds, math.ceil(history[0] + rate.seconds - now)))

        history.append(now)
        cache.set(key, history, rate.cache_timeout)
        return None

    def reset(self, key: str) -> None:
        self._cache.delete(key)
