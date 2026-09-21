from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from apps.catalog.selectors import (
    get_featured_products,
    get_product_detail_by_slug,
    get_product_listing,
)


def home(request: HttpRequest) -> HttpResponse:
    featured_products = get_featured_products()
    return render(request, 'catalog/home.html', {'featured_products': featured_products})


def product_list(request: HttpRequest, category_slug: str | None = None) -> HttpResponse:
    products = get_product_listing(category_slug=category_slug)
    return render(request, 'catalog/product_list.html', {'products': products})


def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_product_detail_by_slug(slug)
    if product is None:
        raise Http404
    return render(request, 'catalog/product_detail.html', {'product': product})
