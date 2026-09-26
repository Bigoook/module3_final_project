"""Review operations; the purchase-and-unique rules live here."""

from typing import Any

from apps.catalog.selectors import can_submit_review
from apps.reviews.models import Review


class ReviewNotAllowedError(ValueError):
    """Raised when the user may not add a review to a product."""


def create_review(*, user: Any, product: Any, rating: int, comment: str) -> Review:
    """Create a review only after the user bought the product and has not reviewed it yet."""
    if not can_submit_review(user, product):
        raise ReviewNotAllowedError('You can only review a product after purchasing it.')
    return Review.objects.create(product=product, user=user, rating=rating, comment=comment)
