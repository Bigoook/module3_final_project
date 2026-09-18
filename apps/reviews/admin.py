from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'user__email')
    list_select_related = ('product', 'user')
    readonly_fields = ('created_at',)
