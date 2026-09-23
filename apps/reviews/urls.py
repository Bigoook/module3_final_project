from django.urls import path

from apps.reviews import views

app_name = 'reviews'

urlpatterns = [
    path('products/<slug:slug>/reviews/create/', views.review_create_placeholder, name='create'),
]
