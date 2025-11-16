from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Single URL that renders different content based on role
    path('', views.dashboard, name='index'),
]