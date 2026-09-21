from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST


def login_view(request: HttpRequest) -> HttpResponseRedirect:
    return HttpResponseRedirect(reverse('catalog:home'))


def register_view(request: HttpRequest) -> HttpResponseRedirect:
    return HttpResponseRedirect(reverse('catalog:home'))


def profile_view(request: HttpRequest) -> HttpResponseRedirect:
    return HttpResponseRedirect(reverse('catalog:home'))


@require_POST
def logout_view(request: HttpRequest) -> HttpResponseRedirect:
    return HttpResponseRedirect(reverse('catalog:home'))
