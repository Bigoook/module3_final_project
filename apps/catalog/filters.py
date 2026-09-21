from django.db.models import Q
from django_filters import CharFilter, FilterSet, NumberFilter  # type: ignore[import-untyped]

from apps.catalog.models import Category, Product


class ProductFilter(FilterSet):
    search = CharFilter(method='filter_search')
    category = CharFilter(method='filter_category')
    min_price = NumberFilter(field_name='price', lookup_expr='gte')
    max_price = NumberFilter(field_name='price', lookup_expr='lte')
    in_stock = CharFilter(method='filter_in_stock')

    class Meta:
        model = Product
        fields = ('search', 'category', 'min_price', 'max_price', 'in_stock')

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(name__icontains=value) | Q(description__icontains=value)
            )
        return queryset

    def filter_category(self, queryset, name, value):
        if value:
            category = Category.objects.filter(slug=value).first()
            if category is None:
                return queryset.none()
            return queryset.filter(category__in=[category, *category.get_descendants()])
        return queryset

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset
