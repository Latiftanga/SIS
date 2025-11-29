"""
URL patterns for the grading application.
"""
from django.urls import path
from . import views

app_name = 'grading'

urlpatterns = [
    # Dashboard
    path('', views.grading_dashboard, name='dashboard'),

    # Grading Periods (Phase 2)
    path('periods/', views.grading_period_list, name='period_list'),
    path('periods/create/', views.grading_period_create, name='period_create'),
    path('periods/<int:pk>/', views.grading_period_detail, name='period_detail'),
    path('periods/<int:pk>/edit/', views.grading_period_edit, name='period_update'),
    path('periods/<int:pk>/delete/', views.grading_period_delete, name='period_delete'),
    path('periods/<int:pk>/set-current/', views.set_current_period, name='set_current_period'),

    # Assessment Types (Phase 2)
    path('assessment-types/', views.assessment_type_list, name='assessment_type_list'),
    path('assessment-types/create/', views.assessment_type_create, name='assessment_type_create'),
    path('assessment-types/<int:pk>/edit/', views.assessment_type_edit, name='assessment_type_update'),
    path('assessment-types/<int:pk>/delete/', views.assessment_type_delete, name='assessment_type_delete'),

    # Subject Assessments (Phase 3)
    path('assessments/', views.assessment_list, name='assessment_list'),
    path('assessments/create/', views.assessment_create, name='assessment_create'),
    path('assessments/<int:pk>/', views.assessment_detail, name='assessment_detail'),
    path('assessments/<int:pk>/edit/', views.assessment_edit, name='assessment_update'),
    path('assessments/<int:pk>/delete/', views.assessment_delete, name='assessment_delete'),
    path('assessments/<int:pk>/publish/', views.publish_assessment, name='publish_assessment'),

    # Grade Entry (Phase 4)
    path('assessments/<int:assessment_id>/enter-grades/', views.grade_entry, name='grade_entry'),
    path('grades/<int:pk>/edit/', views.grade_edit, name='grade_edit'),

    # Term Grades & Calculations (Phase 5)
    path('term-grades/', views.term_grade_list, name='term_grade_list'),
    path('term-grades/calculate/', views.calculate_term_grades, name='calculate_term_grades'),
    path('class/<int:class_id>/term-grades/', views.class_term_grades, name='class_term_grades'),
    path('student/<int:student_id>/term-grades/', views.student_term_grades, name='student_term_grades'),

    # Conduct Grades
    path('conduct/', views.conduct_grade_list, name='conduct_list'),
    path('conduct/class/<int:class_id>/', views.class_conduct_entry, name='conduct_entry'),

    # Report Cards (Phase 6)
    path('report-cards/', views.report_card_list, name='report_card_list'),
    path('report-cards/<int:pk>/', views.report_card_detail, name='report_card_detail'),
    path('report-cards/<int:pk>/pdf/', views.report_card_pdf, name='report_card_pdf'),
    path('report-cards/generate/', views.generate_report_cards, name='generate_report_cards'),
    path('report-cards/<int:pk>/publish/', views.publish_report_card, name='publish_report_card'),
    path('report-cards/class/<int:class_id>/', views.class_report_cards, name='class_report_cards'),
]
