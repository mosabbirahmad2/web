from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Fantacy Tech Superuser Gateway"
admin.site.site_title = "Fantacy Tech Admin"
admin.site.index_title = "Database Administration"

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.BASE_DIR / 'static')
