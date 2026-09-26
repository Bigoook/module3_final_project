"""Aggregated shop analytics for the admin dashboard."""

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, QuerySet, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem
from apps.reviews.models import Review

LOW_STOCK_THRESHOLD = 3
TOP_PRODUCTS_LIMIT = 5
TREND_DAYS = 7


def get_low_stock_products(queryset: QuerySet[Product]) -> QuerySet[Product]:
    """Active products whose remaining stock is at or below the threshold."""
    return queryset.filter(is_active=True, stock__lte=LOW_STOCK_THRESHOLD)


def get_shop_statistics() -> dict[str, Any]:
    """Core figures for the admin analytics page."""
    active_orders = Order.objects.exclude(status=Order.Status.CANCELLED)

    total_revenue = Decimal(active_orders.aggregate(total=Sum('total_price'))['total'] or 0)
    order_count = Order.objects.count()
    average_check = total_revenue / order_count if order_count else Decimal('0')

    top_products = list(
        OrderItem.objects.annotate(line_revenue=F('quantity') * F('price'))
        .values('product__id', 'product__name')
        .annotate(
            sold_quantity=Sum('quantity'),
            revenue=Sum('line_revenue'),
        )
        .order_by('-sold_quantity', '-revenue')[:TOP_PRODUCTS_LIMIT]
    )

    week_ago = timezone.now() - timedelta(days=TREND_DAYS)
    trend = list(
        Order.objects.filter(created_at__gte=week_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(orders=Count('id'), revenue=Sum('total_price'))
        .order_by('day')
    )

    low_stock = list(get_low_stock_products(Product.objects.all()).order_by('stock'))

    return {
        'total_revenue': total_revenue,
        'order_count': order_count,
        'average_check': average_check,
        'pending_orders': Order.objects.filter(status=Order.Status.PENDING).count(),
        'top_products': top_products,
        'low_stock': low_stock,
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'trend': trend,
        'user_count': get_user_model().objects.count(),
        'review_count': Review.objects.count(),
        'average_rating': Review.objects.aggregate(avg=Avg('rating'))['avg'],
    }
