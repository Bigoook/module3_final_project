"""Session cart storage: a {product_id: quantity} map with no business rules."""

from typing import Any

CART_SESSION_KEY = 'cart'


class Cart:
    """Thin wrapper over the session's cart dict. Policies live in services."""

    def __init__(self, session: Any) -> None:
        self.session = session
        self._items: dict[str, int] = session.setdefault(CART_SESSION_KEY, {})

    def save(self) -> None:
        self.session[CART_SESSION_KEY] = self._items
        self.session.modified = True

    def add(self, product_id: int, quantity: int) -> None:
        """Increase the stored quantity for ``product_id``."""
        self._items[str(product_id)] = self._items.get(str(product_id), 0) + quantity
        self.save()

    def set_quantity(self, product_id: int, quantity: int) -> None:
        """Store an exact quantity for ``product_id``."""
        self._items[str(product_id)] = quantity
        self.save()

    def remove(self, product_id: int) -> None:
        """Drop the line for ``product_id``, if present."""
        if self._items.pop(str(product_id), None) is not None:
            self.save()

    def contains(self, product_id: int) -> bool:
        return str(product_id) in self._items

    def get_quantity(self, product_id: int) -> int:
        return self._items.get(str(product_id), 0)

    def count(self) -> int:
        """Total number of units across all lines."""
        return sum(self._items.values())

    def items(self) -> dict[str, int]:
        """Copy of the internal mapping, keyed by string product id."""
        return dict(self._items)

    def clear(self) -> None:
        self._items.clear()
        self.save()
