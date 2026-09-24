import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.orders.models import Order

User = get_user_model()


def _register_url() -> str:
    return reverse('accounts:register')


def _login_url() -> str:
    return reverse('accounts:login')


def _logout_url() -> str:
    return reverse('accounts:logout')


def _profile_url() -> str:
    return reverse('accounts:profile')


def _password_url() -> str:
    return reverse('accounts:password_change')


@pytest.mark.django_db
def test_register_creates_user_and_logs_in(client) -> None:
    response = client.post(
        _register_url(),
        {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'S3cure-pass-123',
            'password2': 'S3cure-pass-123',
        },
    )

    assert response.status_code == 302
    assert response.url == reverse('catalog:home')
    assert User.objects.filter(username='newuser', email='new@example.com').exists()
    assert '_auth_user_id' in client.session


@pytest.mark.django_db
def test_register_rejects_duplicate_email(client) -> None:
    User.objects.create_user(username='first', email='dup@example.com', password='pass')

    response = client.post(
        _register_url(),
        {
            'username': 'second',
            'email': 'dup@example.com',
            'password1': 'S3cure-pass-123',
            'password2': 'S3cure-pass-123',
        },
    )

    assert response.status_code == 200
    assert 'already exists' in response.content.decode()
    assert not User.objects.filter(username='second').exists()


@pytest.mark.django_db
def test_register_rejects_mismatched_passwords(client) -> None:
    response = client.post(
        _register_url(),
        {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'S3cure-pass-123',
            'password2': 'different-pass',
        },
    )

    assert 'The two password fields didn' in response.content.decode()
    assert User.objects.filter(username='newuser').count() == 0


@pytest.mark.django_db
def test_guest_can_view_login_page(client) -> None:
    response = client.get(_login_url())

    assert response.status_code == 200


@pytest.mark.django_db
def test_login_redirects_authenticated_user_to_profile(client) -> None:
    user = User.objects.create_user(username='buyer', password='pass')
    client.force_login(user)

    response = client.get(_login_url())

    assert response.status_code == 302
    assert response.url == reverse('accounts:profile')


@pytest.mark.django_db
def test_login_success_redirects_to_next(client) -> None:
    User.objects.create_user(username='buyer', password='secret-pass-1')

    response = client.post(
        _login_url(),
        {'username': 'buyer', 'password': 'secret-pass-1', 'next': '/cart/'},
    )

    assert response.status_code == 302
    assert response.url == '/cart/'
    assert '_auth_user_id' in client.session


@pytest.mark.django_db
def test_login_ignores_external_next(client) -> None:
    User.objects.create_user(username='buyer', password='secret-pass-1')

    response = client.post(
        _login_url(),
        {'username': 'buyer', 'password': 'secret-pass-1', 'next': 'https://evil.example'},
    )

    assert response.url == '/account/'


@pytest.mark.django_db
def test_login_rejects_bad_credentials(client) -> None:
    User.objects.create_user(username='buyer', password='secret-pass-1')

    response = client.post(
        _login_url(),
        {'username': 'buyer', 'password': 'wrong-password'},
    )

    assert response.status_code == 200
    assert '_auth_user_id' not in client.session


@pytest.mark.django_db
def test_logout_ends_session(client) -> None:
    user = User.objects.create_user(username='buyer', password='pass')
    client.force_login(user)

    response = client.post(_logout_url())

    assert response.status_code == 302
    assert response.url == reverse('catalog:home')
    assert '_auth_user_id' not in client.session


@pytest.mark.django_db
def test_profile_requires_login(client) -> None:
    response = client.get(_profile_url())

    assert response.status_code == 302
    assert reverse('accounts:login') in response.url


@pytest.mark.django_db
def test_profile_update_saves_data(client) -> None:
    user = User.objects.create_user(username='buyer', password='pass')
    client.force_login(user)

    response = client.post(
        _profile_url(),
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+380 12 345 67 89',
            'default_address': 'Khreshchatyk 1, Kyiv',
        },
    )

    assert response.status_code == 302
    assert response.url == _profile_url()
    user.refresh_from_db()
    assert user.first_name == 'John'
    assert user.last_name == 'Doe'
    assert user.phone == '+380 12 345 67 89'
    assert user.default_address == 'Khreshchatyk 1, Kyiv'


@pytest.mark.django_db
def test_password_change_requires_login(client) -> None:
    assert client.get(_password_url()).status_code == 302


@pytest.mark.django_db
def test_password_change_success(client) -> None:
    user = User.objects.create_user(username='buyer', password='old-pass-123')
    client.force_login(user)

    response = client.post(
        _password_url(),
        {
            'old_password': 'old-pass-123',
            'new_password1': 'new-pass-456',
            'new_password2': 'new-pass-456',
        },
    )

    assert response.status_code == 302
    assert response.url == reverse('accounts:password_change_done')
    user.refresh_from_db()
    assert user.check_password('new-pass-456')


@pytest.mark.django_db
def test_order_list_shows_only_own_orders_and_filters(client) -> None:
    owner = User.objects.create_user(username='owner', password='pass')
    other = User.objects.create_user(username='other', password='pass')
    kept = Order.objects.create(
        user=owner,
        full_name='Owner',
        email='owner@example.com',
        phone='+380 12 345 67 89',
        status=Order.Status.PENDING,
    )
    Order.objects.create(
        user=owner,
        full_name='Owner',
        email='owner@example.com',
        phone='+380 12 345 67 89',
        status=Order.Status.SHIPPED,
    )
    foreign_order = Order.objects.create(
        user=other,
        full_name='Other',
        email='other@example.com',
        phone='+380 12 345 67 89',
        status=Order.Status.PENDING,
    )

    client.force_login(owner)
    response = client.get(reverse('orders:order_list'))

    assert response.status_code == 200
    content = response.content.decode()
    assert f'#{kept.id}' in content
    assert f'#{foreign_order.id}' not in content

    filtered = client.get(reverse('orders:order_list'), {'status': 'pending'})
    filtered_content = filtered.content.decode()
    assert f'#{kept.id}' in filtered_content
    assert filtered.context['orders'].count() == 1


@pytest.mark.django_db
def test_order_list_ignores_unknown_status_param(client) -> None:
    owner = User.objects.create_user(username='owner', password='pass')
    Order.objects.create(
        user=owner,
        full_name='Owner',
        email='owner@example.com',
        phone='+380 12 345 67 89',
    )

    client.force_login(owner)
    response = client.get(reverse('orders:order_list'), {'status': 'bogus'})

    assert response.context['orders'].count() == 1
    assert not response.context['current_status']
