# urls_public.py
"""
URL configuration for PUBLIC schema (main domain).
Handles landing page and platform admin.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from schools import views as school_views

urlpatterns = [
    # Platform admin
    path('admin/', admin.site.urls),
    
    # Public landing page
    path('', school_views.index, name='public_index'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)