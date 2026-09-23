from django.urls import path

from apps.orders import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.CartAddView.as_view(), name='cart_add'),
    path('cart/update/<int:product_id>/', views.CartUpdateView.as_view(), name='cart_update'),
    path('cart/remove/<int:product_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
]
