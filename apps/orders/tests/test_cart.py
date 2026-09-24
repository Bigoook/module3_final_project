from apps.orders.cart import CART_SESSION_KEY, Cart


class _FakeSession(dict):
    """Django session lookalike backed by a plain dict."""

    modified = False


def _make_cart() -> tuple[Cart, _FakeSession]:
    session = _FakeSession()
    return Cart(session), session


def test_add_accumulates_quantity() -> None:
    cart, _ = _make_cart()

    cart.add(1, 2)
    cart.add(1, 3)

    assert cart.count() == 5
    assert cart.get_quantity(1) == 5


def test_add_uses_string_product_ids() -> None:
    cart, session = _make_cart()

    cart.add(7, 2)

    assert session[CART_SESSION_KEY] == {'7': 2}


def test_set_quantity_replaces_existing_line() -> None:
    cart, _ = _make_cart()
    cart.add(1, 2)

    cart.set_quantity(1, 7)

    assert cart.count() == 7


def test_set_quantity_inserts_new_line() -> None:
    cart, _ = _make_cart()

    cart.set_quantity(3, 4)

    assert cart.get_quantity(3) == 4


def test_remove_deletes_line() -> None:
    cart, _ = _make_cart()
    cart.add(1, 2)

    cart.remove(1)

    assert cart.count() == 0
    assert not cart.contains(1)


def test_remove_absent_line_is_silent() -> None:
    cart, _ = _make_cart()

    cart.remove(999)

    assert cart.count() == 0


def test_contains_and_get_quantity() -> None:
    cart, _ = _make_cart()

    assert not cart.contains(1)
    assert cart.get_quantity(1) == 0

    cart.add(1, 2)

    assert cart.contains(1)
    assert cart.get_quantity(1) == 2


def test_count_sums_units_across_lines() -> None:
    cart, _ = _make_cart()

    cart.add(1, 2)
    cart.add(2, 3)

    assert cart.count() == 5


def test_items_returns_a_copy() -> None:
    cart, _ = _make_cart()
    cart.add(1, 2)

    snapshot = cart.items()

    assert snapshot == {'1': 2}
    cart.add(1, 1)
    assert snapshot == {'1': 2}


def test_clear_empties_cart() -> None:
    cart, _ = _make_cart()
    cart.add(1, 2)
    cart.add(2, 3)

    cart.clear()

    assert cart.count() == 0
    assert cart.items() == {}


def test_mutations_mark_session_modified() -> None:
    cart, session = _make_cart()

    cart.add(1, 1)

    assert session.modified is True
