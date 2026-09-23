from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse


def review_create_placeholder(request: HttpRequest, slug: str) -> HttpResponseRedirect:
    return HttpResponseRedirect(reverse('catalog:product_detail', kwargs={'slug': slug}))
