from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.views import GuidesRecipesView, health
from config.admin_site import shop_admin_site

urlpatterns = [
    path('admin/', shop_admin_site.urls),
    path('health/', health, name='health'),
    path('guides-recipes/', GuidesRecipesView.as_view(), name='guides_recipes'),
    path('api/', include('apps.api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='api_schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='api_schema'),
        name='api_docs',
    ),
    path('', include('apps.catalog.urls')),
    path('', include('apps.accounts.urls')),
    path('', include('apps.orders.urls')),
    path('', include('apps.reviews.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
