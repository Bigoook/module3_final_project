"""Shared template tags for the shop: money formatting and star ratings."""

from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def money(value) -> str:
    """Format a price as USD, e.g. $12.50."""
    return f'${Decimal(value):.2f}'


@register.simple_tag(is_safe=True)  # type: ignore[call-overload]
def stars(value) -> str:
    """Render a 5-star rating row (full / half / empty FontAwesome 6 icons)."""
    try:
        rating = float(value or 0)
    except (TypeError, ValueError):
        rating = 0.0

    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0

    icons = []
    for index in range(5):
        if index < full:
            icons.append('<i class="fa-solid fa-star"></i>')
        elif index == full and half:
            icons.append('<i class="fa-solid fa-star-half-stroke"></i>')
        else:
            icons.append('<i class="fa-regular fa-star"></i>')
    return ''.join(icons)
