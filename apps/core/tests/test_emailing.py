from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.core.emailing import send_email, send_order_confirmation
from apps.factories import make_product
from apps.orders.models import Order, OrderItem


@pytest.fixture
def order():
    user = get_user_model().objects.create_user(username='buyer')
    return Order.objects.create(
        user=user,
        order_number=7,
        full_name='Test Buyer',
        email='buyer@example.com',
        phone='+380 12 345 67 89',
        shipping_address='Kyiv',
        payment_method='card',
    )


def test_send_email_skips_without_api_key() -> None:
    with override_settings(RESEND_API_KEY=''):
        with patch('apps.core.emailing.resend.Emails.send') as send:
            result = send_email(to='a@example.com', subject='Hi', html='<b>Hi</b>')

    assert result is False
    send.assert_not_called()


def test_send_email_calls_resend_sdk() -> None:
    with override_settings(RESEND_API_KEY='re_123', RESEND_FROM_EMAIL='shop@example.com'):
        with patch('apps.core.emailing.resend.Emails.send') as send:
            result = send_email(to='a@example.com', subject='Hi', html='<b>Hi</b>', text='Hi')

    assert result is True
    send.assert_called_once_with(
        {
            'from': 'shop@example.com',
            'to': ['a@example.com'],
            'subject': 'Hi',
            'html': '<b>Hi</b>',
            'text': 'Hi',
        }
    )


@pytest.mark.django_db
def test_send_order_confirmation_sends_to_customer_only(order) -> None:
    with override_settings(RESEND_API_KEY='re_123', SHOP_EMAIL=''):
        with patch('apps.core.emailing.send_email') as send:
            send_order_confirmation(order)

    send.assert_called_once()
    kwargs = send.call_args.kwargs
    assert kwargs['to'] == 'buyer@example.com'
    assert f'#{order.order_number}' in kwargs['subject']
    assert 'Test Buyer' in kwargs['html']


@pytest.mark.django_db
def test_send_order_confirmation_sends_shop_copy_when_enabled(order) -> None:
    with override_settings(RESEND_API_KEY='re_123', SHOP_EMAIL='admin@example.com'):
        with patch('apps.core.emailing.send_email') as send:
            send_order_confirmation(order)

    assert send.call_count == 2
    recipients = {call.kwargs['to'] for call in send.call_args_list}
    assert recipients == {'buyer@example.com', 'admin@example.com'}


@pytest.mark.django_db
@override_settings(SHOP_NAME='Test Brewery', SHOP_EMAIL='hello@test.example', SHOP_CURRENCY='USD')
def test_order_confirmation_email_uses_shop_settings(order) -> None:
    with override_settings(RESEND_API_KEY='re_123'):
        with patch('apps.core.emailing.send_email') as send:
            send_order_confirmation(order)

    kwargs = send.call_args.kwargs
    assert kwargs['subject'].startswith('Test Brewery — order #7')
    assert '<title>Test Brewery — order #7</title>' in kwargs['html']
    assert 'Test Brewery' in kwargs['html']
    assert 'hello@test.example' in kwargs['html']
    assert '{{' not in kwargs['html']


@pytest.mark.django_db
@override_settings(SHOP_CURRENCY='USD')
def test_order_confirmation_email_formats_prices_with_currency(order) -> None:
    order_item = OrderItem.objects.create(
        order=order,
        product=make_product(price='12.50'),
        quantity=2,
        price='12.50',
    )

    with override_settings(RESEND_API_KEY='re_123'):
        with patch('apps.core.emailing.send_email') as send:
            send_order_confirmation(order)

    html = send.call_args.kwargs['html']
    assert '$25.00' in html
    assert str(order_item.subtotal) not in html
