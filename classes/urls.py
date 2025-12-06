from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    # Subject URLs
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    
    # Class URLs
    path('', views.class_list, name='class_list'),
    path('create/', views.class_create, name='class_create'),
    path('<int:pk>/', views.class_detail, name='class_detail'),
    path('<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('<int:pk>/delete/', views.class_delete, name='class_delete'),
    
    # Class Subject URLs
    path('<int:class_pk>/assign-subject/', views.class_subject_create, name='class_subject_create'),
    path('class-subjects/<int:pk>/delete/', views.class_subject_delete, name='class_subject_delete'),
    
    # Enrollment URLs
    path('<int:class_pk>/enroll-student/', views.enrollment_create, name='enrollment_create'),
    path('<int:class_pk>/enroll-students/', views.enrollment_bulk, name='enrollment_bulk'),
    path('enrollments/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),

    # Promotion/Academic Year Management
    path('<int:class_pk>/promote/', views.class_promote, name='class_promote'),
    path('student/<int:student_pk>/transcript/', views.student_transcript, name='student_transcript'),
    path('student/<int:student_pk>/transcript/pdf/', views.student_transcript_pdf, name='student_transcript_pdf'),

    # House Management URLs
    path('houses/', views.house_list, name='house_list'),
    path('houses/create/', views.house_create, name='house_create'),
    path('houses/<int:pk>/', views.house_detail, name='house_detail'),
    path('houses/<int:pk>/edit/', views.house_edit, name='house_edit'),
    path('houses/<int:pk>/delete/', views.house_delete, name='house_delete'),
]
