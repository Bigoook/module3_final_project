from django.contrib import messages
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import RedirectView, TemplateView

from apps.catalog.models import Product
from apps.orders.cart import Cart
from apps.orders.forms import AddToCartForm
from apps.orders.selectors import get_cart_lines, get_cart_total
from apps.orders.services import (
    CartStatus,
    add_product_to_cart,
    remove_from_cart,
    update_cart_quantity,
)


class CartView(TemplateView):
    """Render the session cart with live prices."""

    template_name = 'orders/cart.html'

    def get_context_data(self, **kwargs):
        cart = Cart(self.request.session)
        lines = get_cart_lines(cart)
        context = super().get_context_data(**kwargs)
        context['lines'] = lines
        context['total'] = get_cart_total(lines)
        context['is_empty'] = not lines
        return context


class CartAddView(View):
    """Add a product (with an optional quantity) to the session cart."""

    http_method_names = ('post',)

    def post(self, request: HttpRequest, product_id: int) -> HttpResponseRedirect:
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        cart = Cart(request.session)

        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
        else:
            quantity = 1
            messages.warning(request, 'Invalid quantity — added 1 item instead.')

        result = add_product_to_cart(cart, product, quantity)
        if result.status == CartStatus.OUT_OF_STOCK:
            messages.error(request, f'"{product.name}" is currently out of stock.')
        else:
            if result.status == CartStatus.CAPPED:
                messages.warning(
                    request,
                    f'Only {result.quantity} of "{product.name}" are in stock.',
                )
            messages.success(
                request,
                f'Added {result.quantity} × "{product.name}" to your cart.',
            )
        return redirect(product.get_absolute_url())


class CartUpdateView(View):
    """Change the quantity of an existing cart line."""

    http_method_names = ('post',)

    def post(self, request: HttpRequest, product_id: int) -> HttpResponseRedirect:
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        cart = Cart(request.session)

        form = AddToCartForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Quantity must be a whole number of at least 1.')
            return redirect('orders:cart')

        result = update_cart_quantity(cart, product, form.cleaned_data['quantity'])
        if result.status == CartStatus.MISSING:
            messages.error(request, 'That product is not in your cart.')
        elif result.status == CartStatus.REMOVED:
            messages.warning(
                request,
                f'"{product.name}" went out of stock and was removed from your cart.',
            )
        else:
            if result.status == CartStatus.CAPPED:
                messages.warning(
                    request,
                    f'Only {result.quantity} of "{product.name}" are in stock.',
                )
            messages.success(
                request,
                f'Updated "{product.name}" quantity to {result.quantity}.',
            )
        return redirect('orders:cart')


class CartRemoveView(View):
    """Remove a line from the session cart."""

    http_method_names = ('post',)

    def post(self, request: HttpRequest, product_id: int) -> HttpResponseRedirect:
        product = get_object_or_404(Product, pk=product_id)
        cart = Cart(request.session)
        remove_from_cart(cart, product)
        messages.success(request, f'Removed "{product.name}" from your cart.')
        return redirect('orders:cart')


class CheckoutView(RedirectView):
    """Placeholder until the checkout flow is implemented (see block 3.4)."""

    pattern_name = 'catalog:home'
