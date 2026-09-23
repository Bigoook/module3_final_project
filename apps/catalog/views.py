from django.http import Http404
from django.views.generic import DetailView, ListView, TemplateView

from apps.catalog.filters import ProductFilter
from apps.catalog.models import Product
from apps.catalog.selectors import (
    can_submit_review,
    get_featured_products,
    get_product_detail_by_slug,
    get_product_listing,
    get_related_products,
)
from apps.orders.forms import AddToCartForm
from apps.reviews.forms import ReviewForm


class HomeView(TemplateView):
    template_name = 'catalog/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = get_featured_products()
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        ordering = self.request.GET.get('ordering', '-created_at')
        queryset = get_product_listing(category_slug=category_slug, ordering=ordering)
        self.filterset = ProductFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None) -> Product:
        product = get_product_detail_by_slug(self.kwargs['slug'])
        if product is None:
            raise Http404('Product not found')
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product: Product = self.object
        context['reviews'] = list(product.reviews.all())
        context['related_products'] = get_related_products(product)
        context['can_review'] = can_submit_review(self.request.user, product)
        context['review_form'] = ReviewForm()
        context['cart_form'] = AddToCartForm()
        return context
