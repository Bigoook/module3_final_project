from django.urls import path

from apps.orders import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
]
