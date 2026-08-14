from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.sitemaps import BlogSitemap, StaticPageSitemap, VendorSitemap

sitemaps = {
    'static': StaticPageSitemap,
    'vendors': VendorSitemap,
    'blog': BlogSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('vendors/', include('apps.vendors.urls')),
    path('bookings/', include('apps.bookings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
