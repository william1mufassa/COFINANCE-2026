from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/credits/', include('credits.urls')),
    path('api/repayments/', include('credits.urls_repayments')),
    path('api/insurance/', include('insurance.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/admin/chat/', include('chat.urls_admin')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

