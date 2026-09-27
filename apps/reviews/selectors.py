"""Read-only review queries."""

from django.db.models import QuerySet

from apps.reviews.models import Review


def list_reviews(product) -> QuerySet[Review]:
    """All published reviews for a product with their authors, newest first."""
    return product.reviews.select_related('user').order_by('-created_at')
