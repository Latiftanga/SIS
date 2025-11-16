from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    # Set the index view to the root path
    path('', views.index_view, name='index'),
]