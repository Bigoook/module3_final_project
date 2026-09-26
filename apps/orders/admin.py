from django.contrib import admin
from django.contrib.admin.decorators import register

from apps.orders.models import Order, OrderItem
from config.admin_site import shop_admin_site


def _status_action(status: str, name: str, description: str):
    @admin.action(description=description)
    def action(modeladmin, request, queryset):
        queryset.update(status=status)

    action.__name__ = name
    return action


mark_as_paid = _status_action(Order.Status.PAID, 'mark_as_paid', 'Mark selected orders as paid')
mark_as_shipped = _status_action(Order.Status.SHIPPED, 'mark_as_shipped', 'Mark selected orders as shipped')
mark_as_delivered = _status_action(Order.Status.DELIVERED, 'mark_as_delivered', 'Mark selected orders as delivered')
mark_as_cancelled = _status_action(Order.Status.CANCELLED, 'mark_as_cancelled', 'Mark selected orders as cancelled')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',)


@register(Order, site=shop_admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'shipping_address')
    list_select_related = ('user',)
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = (OrderItemInline,)
    actions = (mark_as_paid, mark_as_shipped, mark_as_delivered, mark_as_cancelled)


@register(OrderItem, site=shop_admin_site)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_select_related = ('order', 'product')
