"""Shared string helpers."""

from django.utils.text import slugify
from transliterate import translit  # type: ignore[import-untyped]


def make_slug(value: str) -> str:
    """Build an ASCII-safe unique slug, transliterating Cyrillic to Latin."""
    return slugify(translit(value, 'uk', reversed=True))
