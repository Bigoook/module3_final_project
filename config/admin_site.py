"""The shop's customized Django admin site."""

from django.conf import settings
from django.contrib.admin import AdminSite
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import path
from django.utils.translation import gettext_lazy as _

from apps.core.roles import MANAGER_GROUPS
from apps.core.selectors import get_shop_statistics


class ShopAdminSite(AdminSite):
    site_header = f'{settings.SHOP_NAME} Administration'
    site_title = f'{settings.SHOP_NAME} Admin'
    index_title = _('Shop management')
    index_template = 'admin/shop_index.html'

    def has_permission(self, request: HttpRequest) -> bool:
        return (
            request.user.is_active
            and request.user.is_staff
            and (request.user.is_superuser or request.user.groups.filter(name__in=MANAGER_GROUPS).exists())
        )

    def get_urls(self):
        urls = super().get_urls()
        return [path('stats/', self.admin_view(self.stats_view), name='stats')] + urls

    def stats_view(self, request: HttpRequest) -> HttpResponse:
        context = {
            **self.each_context(request),
            'title': _('Shop statistics'),
            'statistics': get_shop_statistics(),
        }
        return render(request, 'admin/shop_stats.html', context)


shop_admin_site = ShopAdminSite(name='shop_admin')
