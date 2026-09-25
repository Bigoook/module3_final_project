from typing import TYPE_CHECKING, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.catalog.models import Product
from apps.core.emailing import send_order_confirmation
from apps.orders.cart import Cart
from apps.orders.forms import AddToCartForm, CheckoutForm
from apps.orders.models import Order
from apps.orders.selectors import get_cart_lines, get_cart_total, get_user_orders
from apps.orders.services import (
    CartStatus,
    OutOfStockError,
    add_product_to_cart,
    create_order,
    remove_from_cart,
    update_cart_quantity,
)

if TYPE_CHECKING:
    from apps.accounts.models import User


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


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Collect delivery data, create the order, and notify by email."""

    template_name = 'orders/checkout.html'

    def get_context_data(self, **kwargs):
        cart = Cart(self.request.session)
        lines = get_cart_lines(cart)
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form') or self._checkout_form()
        context['lines'] = lines
        context['total'] = get_cart_total(lines)
        context['is_empty'] = not lines
        return context

    def _checkout_form(self) -> CheckoutForm:
        user = cast('User', self.request.user)
        full_name = ' '.join(part for part in (user.first_name, user.last_name) if part)
        return CheckoutForm(
            initial={
                'full_name': full_name,
                'email': user.email,
                'phone': user.phone,
                'shipping_address': user.default_address,
            },
        )

    def get(self, request: HttpRequest, *args, **kwargs):
        cart = Cart(request.session)
        if not get_cart_lines(cart):
            messages.info(request, 'Your cart is empty.')
            return redirect('orders:cart')
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs):
        cart = Cart(request.session)
        lines = get_cart_lines(cart)
        if not lines:
            messages.info(request, 'Your cart is empty.')
            return redirect('catalog:home')

        form = CheckoutForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        items = [(line['product'], line['quantity']) for line in lines]
        try:
            order = create_order(
                user=request.user,
                items=items,
                **form.cleaned_data,
            )
        except OutOfStockError as exc:
            messages.error(request, str(exc))
            return self.render_to_response(self.get_context_data(form=form))

        cart.clear()
        send_order_confirmation(order)
        messages.success(
            request,
            f'Order #{order.order_number} placed. A confirmation email is on its way.',
        )
        return redirect('orders:order_detail', pk=order.pk)


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order summary for the owner; doubles as the post-checkout confirmation."""

    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    queryset = Order.objects.select_related('user').prefetch_related('items__product')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class OrderListView(LoginRequiredMixin, ListView):
    """The user's order history with optional status filtering."""

    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        status = self.request.GET.get('status', '')
        return get_user_orders(self.request.user, status=status)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get('status', '')
        context['statuses'] = Order.Status.choices
        context['current_status'] = status if status in Order.Status.values else ''
        return context
