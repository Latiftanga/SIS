# students/urls.py
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student URLs
    path('', views.student_list, name='list'),
    path('create/', views.student_create, name='create'),
    path('<int:pk>/', views.student_detail, name='detail'),
    path('<int:pk>/pdf/', views.student_detail_pdf, name='detail_pdf'),
    path('<int:pk>/edit/', views.student_edit, name='edit'),
    path('<int:pk>/delete/', views.student_delete, name='delete'),
    # Bulk import
    path('bulk-import/', views.student_bulk_import, name='bulk_import'),
    path('bulk-import/process/', views.student_bulk_import_process, name='bulk_import_process'),
    path('download-template/', views.student_download_template, name='download_template'),

    # Programme URLs
    path('programmes/', views.programme_list, name='programme_list'),
    path('programmes/create/', views.programme_create, name='programme_create'),
    path('programmes/<int:pk>/edit/', views.programme_edit, name='programme_edit'),
    path('programmes/<int:pk>/delete/', views.programme_delete, name='programme_delete'),
]
