"""Resend-backed email notifications via the official ``resend`` SDK."""

import logging
from typing import Any

import resend
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_email(*, to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Send a single message via Resend; returns whether it was attempted."""
    api_key = getattr(settings, 'RESEND_API_KEY', '')
    if not api_key:
        logger.warning(
            'RESEND_API_KEY is not set — skipping email to %s ("%s")',
            to,
            subject,
        )
        return False

    params: resend.Emails.SendParams = {
        'from': settings.RESEND_FROM_EMAIL,
        'to': [to],
        'subject': subject,
        'html': html,
    }
    if text:
        params['text'] = text

    resend.api_key = api_key
    try:
        resend.Emails.send(params)
    except resend.exceptions.ResendError:
        logger.exception('Resend request failed for %s', to)
        return False
    return True


def send_order_confirmation(order: Any) -> None:
    """Email the customer and a shop copy with the order summary."""
    subject = f'{settings.SHOP_NAME} — order #{order.order_number}'
    html = render_to_string('emails/order_confirmation.html', {'order': order})
    text = strip_tags(html)

    send_email(to=order.email, subject=subject, html=html, text=text)

    admin_recipient = getattr(settings, 'SHOP_EMAIL', '')
    if admin_recipient and admin_recipient != order.email:
        send_email(
            to=admin_recipient,
            subject=f'{subject} (shop copy)',
            html=html,
            text=text,
        )
