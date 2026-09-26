from django.contrib import admin
from django.contrib.admin.decorators import register

from apps.catalog.models import Category, Product
from apps.catalog.selectors import get_category_options
from apps.core.selectors import get_low_stock_products
from config.admin_site import shop_admin_site


@admin.action(description='Activate selected products')
def activate_products(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description='Deactivate selected products')
def deactivate_products(modeladmin, request, queryset):
    queryset.update(is_active=False)


class CategoryFilter(admin.SimpleListFilter):
    title = 'category'
    parameter_name = 'category'

    def lookups(self, request, model_admin) -> list[tuple[str, str]]:
        return [(str(pk), label) for pk, label in get_category_options()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category_id=self.value())
        return queryset


class LowStockFilter(admin.SimpleListFilter):
    title = 'stock availability'
    parameter_name = 'stock'

    def lookups(self, request, model_admin) -> list[tuple[str, str]]:
        return [('low', 'Low stock')]

    def queryset(self, request, queryset):
        if self.value() == 'low':
            return get_low_stock_products(queryset)
        return queryset


@register(Category, site=shop_admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # ruff: ignore[mutable-class-default]
    ordering = ('name',)


@register(Product, site=shop_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = (CategoryFilter, 'is_active', LowStockFilter)
    list_editable = ('price', 'stock', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}  # ruff: ignore[mutable-class-default]
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('category',)
    actions = (activate_products, deactivate_products)
