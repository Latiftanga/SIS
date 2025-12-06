# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index_or_dashboard, name='index'),  # Root redirect only
    path('settings/', views.settings, name='settings'),
    path('logout/', views.logout_view, name='logout'),
    # Academic Year Management
    path('academic-years/', views.academic_year_list, name='academic_years'),
    path('academic-years/create/', views.academic_year_create, name='academic_year_create'),
    path('academic-years/<int:pk>/edit/', views.academic_year_edit, name='academic_year_edit'),
    path('academic-years/<int:pk>/delete/', views.academic_year_delete, name='academic_year_delete'),
    # Term Management
    path('terms/create/', views.term_create, name='term_create'),
    path('terms/<int:pk>/edit/', views.term_edit, name='term_edit'),
    path('terms/<int:pk>/delete/', views.term_delete, name='term_delete'),
]