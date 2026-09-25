from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
)
from django.contrib.auth.views import (
    LogoutView as DjangoLogoutView,
)
from django.contrib.auth.views import (
    PasswordChangeDoneView as DjangoPasswordChangeDoneView,
)
from django.contrib.auth.views import (
    PasswordChangeView as DjangoPasswordChangeView,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.forms import ProfileForm, RegistrationForm


class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class LogoutView(DjangoLogoutView):
    next_page = '/'


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request: HttpRequest):
        if request.user.is_authenticated:
            return redirect('catalog:home')
        return render(request, self.template_name, {'form': RegistrationForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('catalog:home')
        return render(request, self.template_name, {'form': form})


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form') or ProfileForm(instance=self.request.user)
        return context

    def post(self, request: HttpRequest, *args, **kwargs):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
        return self.render_to_response(self.get_context_data(form=form))


class PasswordChangeView(LoginRequiredMixin, DjangoPasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')


class PasswordChangeDoneView(LoginRequiredMixin, DjangoPasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'
