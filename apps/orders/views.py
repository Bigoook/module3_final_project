from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse


def cart(request: HttpRequest) -> HttpResponseRedirect:
    return HttpResponseRedirect(reverse('catalog:home'))


def cart_add(request: HttpRequest, product_id: int) -> HttpResponseRedirect:
    return HttpResponseRedirect(reverse('catalog:home'))
