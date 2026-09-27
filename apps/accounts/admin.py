from django.contrib import messages
from django.contrib.admin.decorators import register
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.messages import ERROR
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from config.admin_site import shop_admin_site

User = get_user_model()


@register(User, site=shop_admin_site)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            _('Personal info'),
            {'fields': ('first_name', 'last_name', 'email', 'phone', 'default_address')},
        ),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    actions = ('issue_api_token',)

    @staticmethod
    def issue_api_token(modeladmin, request, queryset) -> HttpResponse | None:
        """Print freshly minted JWT access and refresh tokens for one selected user."""
        if queryset.count() != 1:
            messages.add_message(request, ERROR, 'Please select exactly one user to issue a token for.')
            return None
        user = queryset.get()
        refresh = RefreshToken.for_user(user)
        html = render_to_string(
            'admin/api_token.html',
            {'user': user, 'access': str(refresh.access_token), 'refresh': str(refresh)},
            request=request,
        )
        return HttpResponse(html)
