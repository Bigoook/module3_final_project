"""User account operations shared by template views and the API."""

from typing import Any

from django.contrib.auth import get_user_model

User = get_user_model()


def register_user(
    *,
    username: str,
    email: str,
    password: str,
    first_name: str = '',
    last_name: str = '',
    phone: str = '',
    default_address: str = '',
) -> Any:
    """Create and return a new user with a lowercased email."""
    return User.objects.create_user(
        username=username,
        email=email.lower(),
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        default_address=default_address,
    )
