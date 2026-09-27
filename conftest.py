from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError

BASE_DIR = Path(__file__).resolve().parent
LOCALE_DIR = BASE_DIR / 'locale'


def _outdated_catalogs() -> list[Path]:
    """`.po` files whose compiled `.mo` is missing or older than the source."""
    return [
        po
        for po in LOCALE_DIR.glob('*/LC_MESSAGES/*.po')
        if not po.with_suffix('.mo').exists() or po.with_suffix('.mo').stat().st_mtime < po.stat().st_mtime
    ]


@pytest.fixture(scope='session', autouse=True)
def _compiled_translations() -> None:
    """Compile `.po` -> `.mo` before the suite runs.

    `*.mo` is git-ignored, so a fresh checkout (CI, new venv, clean clone) has
    no catalogs and every Ukrainian string would silently fall back to English.
    """
    if not _outdated_catalogs():
        return
    if shutil.which('msgfmt') is None:
        pytest.fail(
            'msgfmt not found: gettext is required to compile translations. '
            'Install it (Windows: choco install gettext; Ubuntu: sudo apt-get install gettext) '
            'or run `manage.py compilemessages` where it is available.'
        )
    locales = sorted(path.name for path in LOCALE_DIR.iterdir() if path.is_dir())
    try:
        for locale in locales:
            call_command('compilemessages', locale=[locale], verbosity=0)
    except CommandError as exc:
        pytest.fail(f'compilemessages failed: {exc}')


@pytest.fixture(autouse=True)
def _reset_throttle_state() -> None:
    """Drop rate-limit counters between tests.

    DRF keeps throttle history in the cache, which is process-wide, so without
    this a busy test could rate-limit the next one.
    """
    cache.clear()
