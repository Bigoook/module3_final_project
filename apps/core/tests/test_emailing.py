from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.core.emailing import send_email, send_order_confirmation
from apps.orders.models import Order


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
