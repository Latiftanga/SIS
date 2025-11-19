# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index_or_dashboard, name='index'),  # Root redirect only
    path('settings/', views.settings, name='settings'),
    path('logout/', views.logout_view, name='logout'),
]