from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard
    path('', views.attendance_dashboard, name='dashboard'),

    # Sessions
    path('sessions/', views.session_list, name='session_list'),
    path('class/<int:class_pk>/create-session/', views.session_create, name='session_create'),
    path('session/<int:session_pk>/', views.session_detail, name='session_detail'),
    path('session/<int:session_pk>/mark/', views.mark_attendance, name='mark_attendance'),
    path('session/<int:session_pk>/delete/', views.session_delete, name='session_delete'),

    # Reports
    path('student/<int:student_pk>/report/', views.student_attendance_report, name='student_report'),
    path('class/<int:class_pk>/report/', views.class_attendance_report, name='class_report'),
]
