"""Reusable query compositions shared by template views and the DRF API."""

from django.db.models import QuerySet

from apps.catalog.models import Product


def get_featured_products(limit: int = 6) -> QuerySet[Product]:
    """Active products with the highest average rating, newest first."""
    return Product.objects.for_listing().order_by('-_rating_avg', '-created_at')[:limit]  # type: ignore[misc]


def get_product_listing(
    *,
    category_slug: str | None = None,
    ordering: str = '-created_at',
) -> QuerySet[Product]:
    """Active products filtered by optional category and ordered."""
    queryset = Product.objects.for_listing()
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    return queryset.order_by(ordering)


def get_product_detail(product_id: int) -> Product | None:
    """Single active product with category and reviews (by primary key)."""

    return (
        Product.objects.for_listing()
        .select_related('category')
        .prefetch_related('reviews__user')
        .filter(pk=product_id)
        .first()
    )


def get_product_detail_by_slug(slug: str) -> Product | None:
    """Single active product with category and reviews (by URL slug)."""

    return (
        Product.objects.for_listing()
        .select_related('category')
        .prefetch_related('reviews__user')
        .filter(slug=slug)
        .first()
    )


def get_related_products(product: Product, limit: int = 4) -> QuerySet[Product]:
    """Other active products from the same category."""
    return (
        Product.objects.for_listing()
        .filter(category=product.category)
        .exclude(pk=product.pk)[:limit]
    )
