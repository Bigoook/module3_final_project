"""Create the admin role groups with their model permissions (idempotent).

Roles:
- "Product Managers" — manage the catalog, view reviews.
- "Order Support" — manage orders and reviews.
"""

from typing import Any

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from apps.catalog.models import Category, Product
from apps.core.roles import GROUP_ORDER_SUPPORT, GROUP_PRODUCT_MANAGERS
from apps.orders.models import Order, OrderItem
from apps.reviews.models import Review


def _permissions(model, *, codes: tuple[str, ...] = ('view', 'add', 'change', 'delete')) -> list[Permission]:
    content_type = ContentType.objects.get_for_model(model)
    return list(
        Permission.objects.filter(
            content_type=content_type,
            codename__in=[f'{code}_{model._meta.model_name}' for code in codes],
        )
    )


def create_roles() -> None:
    product_manager_permissions = _permissions(Product) + _permissions(Category) + _permissions(Review, codes=('view',))
    order_support_permissions = (
        _permissions(Order, codes=('view', 'change'))
        + _permissions(OrderItem, codes=('view',))
        + _permissions(Review, codes=('view', 'change'))
    )

    product_managers, _ = Group.objects.get_or_create(name=GROUP_PRODUCT_MANAGERS)
    product_managers.permissions.set(product_manager_permissions)

    order_support, _ = Group.objects.get_or_create(name=GROUP_ORDER_SUPPORT)
    order_support.permissions.set(order_support_permissions)


class Command(BaseCommand):
    help = _('Creates the admin role groups with their model permissions (idempotent).')

    def handle(self, *args: Any, **options: Any) -> None:
        create_roles()
        self.stdout.write(
            self.style.SUCCESS(
                _('Done: "%(product_manager)s" and "%(order_support)s" are configured.')
                % {'product_manager': GROUP_PRODUCT_MANAGERS, 'order_support': GROUP_ORDER_SUPPORT}
            )
        )
