# teachers/urls.py (create new file)
from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('create/', views.teacher_create, name='create'),
    path('<int:pk>/', views.teacher_detail, name='detail'),
    path('<int:pk>/export-pdf/', views.teacher_export_pdf, name='export_pdf'),
    path('<int:pk>/delete/', views.teacher_delete, name='delete'),
    # Bulk import
    path('bulk-import/', views.teacher_bulk_import, name='bulk_import'),
    path('bulk-import/process/', views.teacher_bulk_import_process, name='bulk_import_process'),
    path('download-template/', views.teacher_download_template, name='download_template'),
]