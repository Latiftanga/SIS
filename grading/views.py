"""
Views for the grading application.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import Q, Count, Avg
from django.db import transaction
from decimal import Decimal

from .models import (
    GradingPeriod, AssessmentType, SubjectAssessment,
    StudentGrade, GradingScale, TermGrade,
    ConductGrade, ReportCard
)
from .forms import (
    GradingPeriodForm, AssessmentTypeForm, SubjectAssessmentForm,
    StudentGradeForm, ConductGradeForm
)
from accounts.decorators import school_admin_required
from classes.models import Class, ClassSubject, StudentEnrollment


# ============ Dashboard ============

@school_admin_required
def grading_dashboard(request: HttpRequest) -> HttpResponse:
    """Grading system dashboard"""
    current_period = GradingPeriod.objects.filter(is_current=True).first()

    context = {
        'current_period': current_period,
        'periods_count': GradingPeriod.objects.filter(is_active=True).count(),
        'assessment_types_count': AssessmentType.objects.filter(is_active=True).count(),
        'pending_assessments': SubjectAssessment.objects.filter(
            grading_period=current_period,
            is_published=False
        ).count() if current_period else 0,
    }

    return render(request, 'grading/dashboard.html', context)


# ============ Grading Period Views ============

@school_admin_required
def grading_period_list(request: HttpRequest) -> HttpResponse:
    """List all grading periods"""
    periods = GradingPeriod.objects.select_related('term__academic_year').order_by('-term__academic_year__start_date', '-term__number')

    # Filter by status
    status = request.GET.get('status', 'all')
    if status == 'active':
        periods = periods.filter(is_active=True)
    elif status == 'current':
        periods = periods.filter(is_current=True)

    # Search
    search = request.GET.get('search', '')
    if search:
        periods = periods.filter(term__academic_year__name__icontains=search)

    # Get all terms for the create modal
    from core.models import Term
    terms = Term.objects.select_related('academic_year').order_by('-academic_year__start_date', 'number')

    # Calculate statistics
    all_periods = GradingPeriod.objects.select_related('term__academic_year').all()
    active_count = all_periods.filter(is_active=True).count()
    current_period = all_periods.filter(is_current=True).first()

    context = {
        'periods': periods,
        'search': search,
        'status': status,
        'terms': terms,
        'active_count': active_count,
        'current_period': current_period,
    }

    return render(request, 'grading/period_list.html', context)


@school_admin_required
def grading_period_create(request: HttpRequest) -> HttpResponse:
    """Create a new grading period"""
    if request.method == 'POST':
        form = GradingPeriodForm(request.POST)
        if form.is_valid():
            period = form.save()
            messages.success(
                request,
                f'Grading period "{period.term}" created successfully!'
            )
            return redirect('grading:period_list')
    else:
        form = GradingPeriodForm()

    return render(request, 'grading/period_form.html', {
        'form': form,
        'action': 'Create'
    })


@school_admin_required
def grading_period_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View grading period details"""
    period = get_object_or_404(GradingPeriod, pk=pk)

    # Get statistics for this period
    assessments = SubjectAssessment.objects.filter(grading_period=period)

    context = {
        'period': period,
        'total_assessments': assessments.count(),
        'published_assessments': assessments.filter(is_published=True).count(),
        'exam_assessments': assessments.filter(assessment_type__is_exam=True).count(),
    }

    return render(request, 'grading/period_detail.html', context)


@school_admin_required
def grading_period_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a grading period"""
    period = get_object_or_404(GradingPeriod, pk=pk)

    if request.method == 'POST':
        form = GradingPeriodForm(request.POST, instance=period)
        if form.is_valid():
            period = form.save()
            messages.success(
                request,
                f'Grading period "{period.term}" updated successfully!'
            )
            return redirect('grading:period_list')
    else:
        form = GradingPeriodForm(instance=period)

    return render(request, 'grading/period_form.html', {
        'form': form,
        'period': period,
        'action': 'Edit'
    })


@school_admin_required
@require_POST
def grading_period_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a grading period"""
    period = get_object_or_404(GradingPeriod, pk=pk)

    # Check if period has assessments
    if SubjectAssessment.objects.filter(grading_period=period).exists():
        messages.error(
            request,
            'Cannot delete this grading period because it has associated assessments.'
        )
        return redirect('grading:period_detail', pk=pk)

    period_name = f"{period.term}"
    period.delete()
    messages.success(request, f'Grading period "{period_name}" deleted successfully!')

    return redirect('grading:period_list')


@school_admin_required
@require_POST
def set_current_period(request: HttpRequest, pk: int) -> HttpResponse:
    """Set a grading period as current"""
    period = get_object_or_404(GradingPeriod, pk=pk)

    # Set this period as current (model's save method handles unsetting others)
    period.is_current = True
    period.save()

    messages.success(
        request,
        f'"{period.term}" is now the current grading period.'
    )

    return redirect('grading:period_list')


# ============ Assessment Type Views ============

@school_admin_required
def assessment_type_list(request: HttpRequest) -> HttpResponse:
    """List all assessment types"""
    assessment_types = AssessmentType.objects.all().order_by('name')

    # Filter by status
    status = request.GET.get('status', 'active')
    if status == 'active':
        assessment_types = assessment_types.filter(is_active=True)
    elif status == 'inactive':
        assessment_types = assessment_types.filter(is_active=False)

    # Filter by type
    type_filter = request.GET.get('type', 'all')
    if type_filter == 'exam':
        assessment_types = assessment_types.filter(is_exam=True)
    elif type_filter == 'continuous':
        assessment_types = assessment_types.filter(is_exam=False)

    context = {
        'assessment_types': assessment_types,
        'status': status,
        'type_filter': type_filter,
    }

    return render(request, 'grading/assessment_type_list.html', context)


@school_admin_required
def assessment_type_create(request: HttpRequest) -> HttpResponse:
    """Create a new assessment type"""
    if request.method == 'POST':
        form = AssessmentTypeForm(request.POST)
        if form.is_valid():
            assessment_type = form.save()
            messages.success(request, f'Assessment type "{assessment_type.name}" created successfully!')
            return redirect('grading:assessment_type_list')
    else:
        form = AssessmentTypeForm()

    return render(request, 'grading/assessment_type_form.html', {
        'form': form,
        'action': 'Create'
    })


@school_admin_required
def assessment_type_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit an assessment type"""
    assessment_type = get_object_or_404(AssessmentType, pk=pk)

    if request.method == 'POST':
        form = AssessmentTypeForm(request.POST, instance=assessment_type)
        if form.is_valid():
            assessment_type = form.save()
            messages.success(request, f'Assessment type "{assessment_type.name}" updated successfully!')
            return redirect('grading:assessment_type_list')
    else:
        form = AssessmentTypeForm(instance=assessment_type)

    return render(request, 'grading/assessment_type_form.html', {
        'form': form,
        'assessment_type': assessment_type,
        'action': 'Edit'
    })


@school_admin_required
@require_POST
def assessment_type_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete an assessment type"""
    assessment_type = get_object_or_404(AssessmentType, pk=pk)

    # Check if assessment type has assessments
    if SubjectAssessment.objects.filter(assessment_type=assessment_type).exists():
        messages.error(
            request,
            'Cannot delete this assessment type because it has associated assessments.'
        )
        return redirect('grading:assessment_type_list')

    name = assessment_type.name
    assessment_type.delete()
    messages.success(request, f'Assessment type "{name}" deleted successfully!')

    return redirect('grading:assessment_type_list')


# ============ Placeholder Views for Future Phases ============
# These will be implemented in subsequent phases

@school_admin_required
def assessment_list(request: HttpRequest) -> HttpResponse:
    """List assessments - Phase 3"""
    return render(request, 'grading/coming_soon.html', {
        'feature': 'Assessment Management',
        'phase': 'Phase 3'
    })


@school_admin_required
def assessment_create(request: HttpRequest) -> HttpResponse:
    """Create assessment - Phase 3"""
    return redirect('grading:assessment_list')


@school_admin_required
def assessment_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Assessment detail - Phase 3"""
    return redirect('grading:assessment_list')


@school_admin_required
def assessment_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit assessment - Phase 3"""
    return redirect('grading:assessment_list')


@school_admin_required
@require_POST
def assessment_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete assessment - Phase 3"""
    return redirect('grading:assessment_list')


@school_admin_required
@require_POST
def publish_assessment(request: HttpRequest, pk: int) -> HttpResponse:
    """Publish assessment - Phase 3"""
    return redirect('grading:assessment_list')


@school_admin_required
def grade_entry(request: HttpRequest, assessment_id: int) -> HttpResponse:
    """Grade entry - Phase 4"""
    return render(request, 'grading/coming_soon.html', {
        'feature': 'Grade Entry',
        'phase': 'Phase 4'
    })


@school_admin_required
def grade_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit grade - Phase 4"""
    return redirect('grading:dashboard')


@school_admin_required
def term_grade_list(request: HttpRequest) -> HttpResponse:
    """Term grades list - Phase 5"""
    return render(request, 'grading/coming_soon.html', {
        'feature': 'Term Grades',
        'phase': 'Phase 5'
    })


@school_admin_required
@require_POST
def calculate_term_grades(request: HttpRequest) -> HttpResponse:
    """Calculate term grades - Phase 5"""
    return redirect('grading:term_grade_list')


@school_admin_required
def class_term_grades(request: HttpRequest, class_id: int) -> HttpResponse:
    """Class term grades - Phase 5"""
    return redirect('grading:term_grade_list')


@school_admin_required
def student_term_grades(request: HttpRequest, student_id: int) -> HttpResponse:
    """Student term grades - Phase 5"""
    return redirect('grading:term_grade_list')


@school_admin_required
def conduct_grade_list(request: HttpRequest) -> HttpResponse:
    """Conduct grades list - Phase 5"""
    return render(request, 'grading/coming_soon.html', {
        'feature': 'Conduct Grades',
        'phase': 'Phase 5'
    })


@school_admin_required
def class_conduct_entry(request: HttpRequest, class_id: int) -> HttpResponse:
    """Class conduct entry - Phase 5"""
    return redirect('grading:conduct_list')


@school_admin_required
def report_card_list(request: HttpRequest) -> HttpResponse:
    """Report cards list - Phase 6"""
    return render(request, 'grading/coming_soon.html', {
        'feature': 'Report Cards',
        'phase': 'Phase 6'
    })


@school_admin_required
def report_card_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Report card detail - Phase 6"""
    return redirect('grading:report_card_list')


@school_admin_required
def report_card_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    """Report card PDF - Phase 6"""
    return redirect('grading:report_card_list')


@school_admin_required
@require_POST
def generate_report_cards(request: HttpRequest) -> HttpResponse:
    """Generate report cards - Phase 6"""
    return redirect('grading:report_card_list')


@school_admin_required
@require_POST
def publish_report_card(request: HttpRequest, pk: int) -> HttpResponse:
    """Publish report card - Phase 6"""
    return redirect('grading:report_card_list')


@school_admin_required
def class_report_cards(request: HttpRequest, class_id: int) -> HttpResponse:
    """Class report cards - Phase 6"""
    return redirect('grading:report_card_list')
