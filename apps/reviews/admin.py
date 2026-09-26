from django.contrib import admin
from django.contrib.admin.decorators import register

from apps.reviews.models import Review
from config.admin_site import shop_admin_site


@register(Review, site=shop_admin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'user__email')
    list_select_related = ('product', 'user')
    readonly_fields = ('created_at',)
