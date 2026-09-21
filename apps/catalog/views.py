from django.http import Http404
from django.views.generic import DetailView, ListView, TemplateView

from apps.catalog.models import Product
from apps.catalog.selectors import (
    get_featured_products,
    get_product_detail_by_slug,
    get_product_listing,
)


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
        return get_product_listing(category_slug=category_slug, ordering=ordering)


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
        context['reviews'] = list(self.object.reviews.all())
        return context
