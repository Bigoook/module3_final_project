from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse

from apps.catalog.models import Category
from apps.core.roles import GROUP_ORDER_SUPPORT, GROUP_PRODUCT_MANAGERS
from apps.core.selectors import get_shop_statistics
from apps.factories import make_product
from apps.orders.models import Order, OrderItem

User = get_user_model()


def _admin(name: str, **kwargs) -> str:
    return reverse(f'shop_admin:{name}', **kwargs)


def _add_to_group(user, group_name: str) -> None:
    call_command('setup_roles')
    user.groups.add(Group.objects.get(name=group_name))


@pytest.mark.django_db
def test_anonymous_admin_redirects_to_login(client) -> None:
    response = client.get(_admin('index'))

    assert response.status_code == 302
    assert 'login' in response.url


@pytest.mark.django_db
def test_non_staff_user_cannot_access_admin(client) -> None:
    user = User.objects.create_user(username='buyer', password='pass')
    client.force_login(user)

    response = client.get(_admin('index'))

    assert response.status_code == 302


@pytest.mark.django_db
def test_superuser_opens_index_and_stats(client) -> None:
    superuser = User.objects.create_superuser(username='boss', password='pass')
    client.force_login(superuser)

    index = client.get(_admin('index'))
    assert index.status_code == 200
    assert index.content.decode().count(f'href="{_admin("stats")}"') > 0

    stats = client.get(_admin('stats'))
    assert stats.status_code == 200
    assert 'Total revenue' in stats.content.decode()


@pytest.mark.django_db
def test_product_manager_accesses_catalog_but_not_orders(client) -> None:
    user = User.objects.create_user(username='pm', password='pass', is_staff=True)
    _add_to_group(user, GROUP_PRODUCT_MANAGERS)
    make_product()
    client.force_login(user)

    assert client.get(_admin('index')).status_code == 200
    assert client.get(_admin('catalog_product_changelist')).status_code == 200
    assert client.get(_admin('orders_order_changelist')).status_code == 403


@pytest.mark.django_db
def test_order_support_accesses_orders_but_not_catalog(client) -> None:
    user = User.objects.create_user(username='support', password='pass', is_staff=True)
    _add_to_group(user, GROUP_ORDER_SUPPORT)
    client.force_login(user)

    assert client.get(_admin('orders_order_changelist')).status_code == 200
    assert client.get(_admin('orders_orderitem_changelist')).status_code == 200
    assert client.get(_admin('catalog_product_changelist')).status_code == 403


@pytest.mark.django_db
def test_setup_roles_grants_expected_permissions() -> None:
    call_command('setup_roles')

    pm = Group.objects.get(name=GROUP_PRODUCT_MANAGERS)
    assert pm.permissions.filter(codename='add_product').exists()
    assert pm.permissions.filter(codename='change_product').exists()
    assert pm.permissions.filter(codename='view_review').exists()
    assert not pm.permissions.filter(codename='change_order').exists()

    support_group = Group.objects.get(name=GROUP_ORDER_SUPPORT)
    assert support_group.permissions.filter(codename='change_order').exists()
    assert support_group.permissions.filter(codename='view_review').exists()
    assert not support_group.permissions.filter(codename='add_product').exists()


@pytest.mark.django_db
def test_product_active_toggle_actions(client) -> None:
    superuser = User.objects.create_superuser(username='boss', password='pass')
    client.force_login(superuser)
    product = make_product(is_active=False)

    response = client.post(
        _admin('catalog_product_changelist'),
        {'action': 'activate_products', '_selected_action': str(product.pk)},
    )

    assert response.status_code == 302
    product.refresh_from_db()
    assert product.is_active

    response = client.post(
        _admin('catalog_product_changelist'),
        {'action': 'deactivate_products', '_selected_action': str(product.pk)},
    )
    assert response.status_code == 302
    product.refresh_from_db()
    assert not product.is_active


@pytest.mark.django_db
def test_mark_order_status_actions(client) -> None:
    superuser = User.objects.create_superuser(username='boss', password='pass')
    client.force_login(superuser)
    buyer = User.objects.create_user(username='buyer', password='pass')
    order = Order.objects.create(
        user=buyer,
        full_name='Buyer',
        email='buyer@example.com',
        phone='+380 12 345 67 89',
    )

    response = client.post(
        _admin('orders_order_changelist'),
        {'action': 'mark_as_paid', '_selected_action': str(order.pk)},
    )
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    client.post(
        _admin('orders_order_changelist'),
        {'action': 'mark_as_cancelled', '_selected_action': str(order.pk)},
    )
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED


@pytest.mark.django_db
def test_low_stock_filter_filters_products(client) -> None:
    superuser = User.objects.create_superuser(username='boss', password='pass')
    client.force_login(superuser)
    low = make_product(name='Low', stock=2)
    make_product(name='Plenty', stock=50)

    response = client.get(_admin('catalog_product_changelist'), {'stock': 'low'})

    content = response.content.decode()
    assert low.name in content
    assert 'Plenty' not in content


@pytest.mark.django_db
def test_product_category_filter_shows_hierarchy(client) -> None:
    superuser = User.objects.create_superuser(username='boss', password='pass')
    client.force_login(superuser)
    parent = Category.objects.create(name='Malts', slug='malts')
    child = Category.objects.create(name='Base Malts', slug='base-malts', parent=parent)
    Category.objects.create(name='Pilsner Malts', slug='pilsner-malts', parent=child)

    response = client.get(_admin('catalog_product_changelist'))

    content = response.content.decode()
    assert content.index('>Malts<') < content.index('— Base Malts') < content.index('— — Pilsner Malts')


@pytest.mark.django_db
def test_statistics_aggregations() -> None:
    boss = User.objects.create_superuser(username='boss', password='pass')
    buyer = User.objects.create_user(username='buyer', password='pass')
    product_a = make_product(name='AAA', price='10.00', stock=5)
    product_b = make_product(name='BBB', price='20.00', stock=5)

    kept = Order.objects.create(user=buyer, full_name='Buyer', email='buyer@example.com', total_price=Decimal('40.00'))
    OrderItem.objects.create(order=kept, product=product_a, quantity=2, price=Decimal('10.00'))
    OrderItem.objects.create(order=kept, product=product_b, quantity=1, price=Decimal('20.00'))
    Order.objects.create(
        user=buyer,
        full_name='Buyer',
        email='buyer@example.com',
        total_price=Decimal('999.00'),
        status=Order.Status.CANCELLED,
    )

    stats = get_shop_statistics()

    assert stats['total_revenue'] == Decimal('40.00')
    assert stats['order_count'] == 2
    assert stats['average_check'] == Decimal('20.00')
    assert stats['pending_orders'] == 1
    top = {row['product__name']: row['sold_quantity'] for row in stats['top_products']}
    assert top == {'AAA': 2, 'BBB': 1}
    assert stats['user_count'] == 2
