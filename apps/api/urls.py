from django.urls import path

from apps.api import views

app_name = 'api'

urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/reviews/', views.ReviewListCreateView.as_view(), name='product_reviews'),
    path('orders/', views.OrderListCreateView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('users/register/', views.RegisterView.as_view(), name='user_register'),
    path('users/login/', views.ThrottledTokenObtainPairView.as_view(), name='user_login'),
    path('users/refresh/', views.ThrottledTokenRefreshView.as_view(), name='user_refresh'),
    path('cart/', views.CartView.as_view(), name='cart'),
]
