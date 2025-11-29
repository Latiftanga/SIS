from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('accounts.urls')),
    path('', include('dashboard.urls')),  # Dashboard app
    path('teachers/', include('teachers.urls')),
    path('students/', include('students.urls')),
    path('classes/', include('classes.urls')),
    path('attendance/', include('attendance.urls')),
    path('grading/', include('grading.urls')),
    path('', include('core.urls')),  # Core utilities (must be last)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)