from django.urls import path

from apps.catalog.views import HomeView, ProductDetailView, ProductListView

app_name = 'catalog'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]
