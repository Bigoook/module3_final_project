from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from apps.catalog.models import Product
from apps.catalog.selectors import (
    get_product_detail_by_slug,
    get_product_page_context,
)
from apps.orders.forms import AddToCartForm
from apps.reviews.forms import ReviewForm
from apps.reviews.services import ReviewNotAllowedError, create_review


class ReviewCreateView(LoginRequiredMixin, FormView):
    """Create a review for a purchased product. The UI only posts to it."""

    template_name = 'catalog/product_detail.html'
    form_class = ReviewForm

    _product: Product

    def get_product(self) -> Product:
        """Resolve the reviewed product once per request, raising 404 if absent."""
        if not hasattr(self, '_product'):
            product = get_product_detail_by_slug(self.kwargs['slug'])
            if product is None:
                raise Http404('Product not found')
            self._product = product
        return self._product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_product()
        context['product'] = product
        context.update(get_product_page_context(product, self.request.user))
        context['review_form'] = context['form']
        context['cart_form'] = AddToCartForm()
        return context

    def form_valid(self, form):
        product = self.get_product()
        try:
            create_review(
                user=self.request.user,
                product=product,
                rating=form.cleaned_data['rating'],
                comment=form.cleaned_data['comment'],
            )
        except ReviewNotAllowedError:
            messages.error(
                self.request,
                'You can only review a product after purchasing it.',
            )
            return redirect(self.get_success_url())
        messages.success(self.request, 'Thank you! Your review has been published.')
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse('catalog:product_detail', kwargs={'slug': self._product.slug})
