from django import forms
from django.core.validators import RegexValidator

from apps.orders.models import Order

PHONE_VALIDATOR = RegexValidator(
    regex=r'^[+0-9()\-\s]{6,32}$',
    message='Enter a valid phone number (digits, +, -, spaces, parentheses).',
)


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)


class CheckoutForm(forms.Form):
    """Contact and delivery data collected at checkout."""

    full_name = forms.CharField(min_length=2, max_length=255)
    email = forms.EmailField()
    phone = forms.CharField(max_length=32, validators=[PHONE_VALIDATOR])
    shipping_address = forms.CharField(widget=forms.Textarea)
    payment_method = forms.ChoiceField(
        choices=Order.PaymentMethod.choices,
        widget=forms.RadioSelect,
        initial=Order.PaymentMethod.CARD,
    )
