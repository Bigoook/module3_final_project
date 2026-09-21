from django.contrib import admin

from apps.catalog.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # ruff: ignore[mutable-class-default]
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    list_editable = ('price', 'stock', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}  # ruff: ignore[mutable-class-default]
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('category',)
