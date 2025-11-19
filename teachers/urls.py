# teachers/urls.py (create new file)
from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('create/', views.teacher_create, name='create'),
    path('<int:pk>/', views.teacher_detail, name='detail'),
    path('<int:pk>/delete/', views.teacher_delete, name='delete'),
]