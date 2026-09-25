from django.urls import path

from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('account/', views.ProfileView.as_view(), name='profile'),
    path('account/password/', views.PasswordChangeView.as_view(), name='password_change'),
    path('account/password/done/', views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
