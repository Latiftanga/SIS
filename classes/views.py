from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, HttpResponse
from django.db.models import Q, Count, Prefetch
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from .models import Subject, Class, ClassSubject, StudentEnrollment, House
from .forms import (
    SubjectForm, ClassForm, ClassSubjectForm,
    StudentEnrollmentForm, BulkEnrollmentForm, HouseForm
)
from .utils import htmx_success_response, htmx_error_response, htmx_success_message
from accounts.decorators import school_admin_required


# ============ Subject Views ============

@school_admin_required
def subject_list(request: HttpRequest) -> HttpResponse:
    """List all subjects"""
    subjects = Subject.objects.all()

    # Status filter
    status = request.GET.get('status', 'active')
    if status == 'active':
        subjects = subjects.filter(is_active=True)
    elif status == 'inactive':
        subjects = subjects.filter(is_active=False)

    # Search
    search = request.GET.get('search', '')
    if search:
        subjects = subjects.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )

    context = {
        'subjects': subjects,
        'search': search,
        'status': status,
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'classes/partials/subject_list_content.html', context)

    return render(request, 'classes/subject_list.html', context)


@school_admin_required
def subject_create(request: HttpRequest) -> HttpResponse:
    """Create a new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" created successfully!')
            return redirect('classes:subject_list')
    else:
        form = SubjectForm()

    context = {
        'form': form,
        'action': 'Create'
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'classes/partials/subject_form_content.html', context)

    return render(request, 'classes/subject_form.html', context)


@school_admin_required
def subject_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a subject"""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f'Subject "{subject.name}" updated successfully!')
            return redirect('classes:subject_list')
    else:
        form = SubjectForm(instance=subject)

    context = {
        'form': form,
        'subject': subject,
        'action': 'Edit'
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'classes/partials/subject_form_content.html', context)

    return render(request, 'classes/subject_form.html', context)


@school_admin_required
@require_http_methods(["DELETE"])
def subject_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft delete a subject"""
    subject = get_object_or_404(Subject, pk=pk)
    subject.is_active = False
    subject.save()
    
    return HttpResponse(headers={'HX-Trigger': 'subjectDeleted'})


# ============ Class Views ============

@school_admin_required
def class_list(request: HttpRequest) -> HttpResponse:
    """List all classes"""
    classes = Class.objects.select_related(
        'class_teacher',
        'academic_year',
        'programme'
    ).annotate(
        student_count=Count('enrollments', filter=Q(enrollments__is_active=True))
    )

    # Status filter
    status = request.GET.get('status', 'active')
    if status == 'active':
        classes = classes.filter(is_active=True)
    elif status == 'inactive':
        classes = classes.filter(is_active=False)

    # Grade filter
    grade = request.GET.get('grade', '')
    if grade:
        classes = classes.filter(grade_level=grade)

    # Search
    search = request.GET.get('search', '')
    if search:
        classes = classes.filter(
            Q(name__icontains=search) |
            Q(grade_level__icontains=search) |
            Q(section__icontains=search)
        )

    # Get unique grades for filter
    grades = Class.objects.filter(is_active=True).values_list('grade_level', flat=True).distinct()

    context = {
        'classes': classes,
        'search': search,
        'status': status,
        'grade': grade,
        'grades': grades,
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/class_list_content.html', context)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/class_list.html', context)


@school_admin_required
def class_create(request: HttpRequest) -> HttpResponse:
    """Create a new class"""
    from django.core.exceptions import ValidationError

    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            try:
                class_obj = form.save()
                messages.success(request, f'Class "{class_obj.name}" created successfully!')

                # For HTMX requests, redirect to class list
                if request.headers.get('HX-Request'):
                    response = HttpResponse()
                    response['HX-Redirect'] = '/classes/'
                    return response

                return redirect('classes:class_list')
            except ValidationError as e:
                # Handle validation errors from model's clean() method
                if hasattr(e, 'error_dict'):
                    for field, errors in e.error_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, e)
        # If form is invalid and HTMX, return the form with errors
        if request.headers.get('HX-Request'):
            response = render(request, 'classes/partials/class_form_content.html', {
                'form': form,
                'action': 'Create'
            })
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
    else:
        form = ClassForm()

    # For HTMX requests, return partial template
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/class_form_content.html', {
            'form': form,
            'action': 'Create'
        })
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/class_form.html', {
        'form': form,
        'action': 'Create'
    })


@school_admin_required
def class_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View class details with students and subjects"""
    class_obj = get_object_or_404(
        Class.objects.select_related('class_teacher'),
        pk=pk
    )

    # Get enrolled students
    enrollments = class_obj.enrollments.filter(
        is_active=True
    ).select_related('student')

    # Get assigned subjects
    subjects = class_obj.class_subjects.filter(
        is_active=True
    ).select_related('subject', 'teacher')

    context = {
        'class': class_obj,
        'enrollments': enrollments,
        'subjects': subjects,
        'student_count': enrollments.count(),
        'available_capacity': class_obj.get_available_capacity(),
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/class_detail_content.html', context)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/class_detail.html', context)


@school_admin_required
def class_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a class"""
    from django.core.exceptions import ValidationError

    class_obj = get_object_or_404(Class, pk=pk)

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            try:
                class_obj = form.save()
                messages.success(request, f'Class "{class_obj.name}" updated successfully!')

                # For HTMX requests, redirect to class detail
                if request.headers.get('HX-Request'):
                    response = HttpResponse()
                    response['HX-Redirect'] = f'/classes/{class_obj.pk}/'
                    return response

                return redirect('classes:class_detail', pk=class_obj.pk)
            except ValidationError as e:
                # Handle validation errors from model's clean() method
                if hasattr(e, 'error_dict'):
                    for field, errors in e.error_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    form.add_error(None, e)
        # If form is invalid and HTMX, return the form with errors
        if request.headers.get('HX-Request'):
            response = render(request, 'classes/partials/class_form_content.html', {
                'form': form,
                'class': class_obj,
                'action': 'Edit'
            })
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
    else:
        form = ClassForm(instance=class_obj)

    # For HTMX requests, return partial template
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/class_form_content.html', {
            'form': form,
            'class': class_obj,
            'action': 'Edit'
        })
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/class_form.html', {
        'form': form,
        'class': class_obj,
        'action': 'Edit'
    })


@school_admin_required
@require_http_methods(["DELETE"])
def class_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft delete a class"""
    class_obj = get_object_or_404(Class, pk=pk)
    class_obj.is_active = False
    class_obj.save()
    
    return HttpResponse(headers={'HX-Trigger': 'classDeleted'})


# ============ Class Subject Views ============

@school_admin_required
def class_subject_create(request: HttpRequest, class_pk: int) -> HttpResponse:
    """Assign a subject to a class"""
    from django.urls import reverse

    class_obj = get_object_or_404(Class, pk=class_pk)
    is_htmx = request.headers.get('HX-Request') == 'true'

    if request.method == 'POST':
        form = ClassSubjectForm(request.POST, class_obj=class_obj)
        if form.is_valid():
            class_subject = form.save(commit=False)
            class_subject.class_obj = class_obj  # Explicitly set the class
            class_subject.save()

            if is_htmx:
                # For HTMX requests, return a success message and trigger modal close + page reload
                messages.success(
                    request,
                    f'Subject "{class_subject.subject.name}" assigned to {class_obj.name}!'
                )
                response = HttpResponse(
                    '<div class="alert alert-success">'
                    '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">'
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />'
                    '</svg>'
                    f'<span>Subject "{class_subject.subject.name}" assigned successfully!</span>'
                    '</div>'
                )
                # Trigger modal close and page reload
                response['HX-Trigger'] = 'closeModal, reload'
                return response
            else:
                # For regular requests, redirect to class detail with subjects tab active
                messages.success(
                    request,
                    f'Subject "{class_subject.subject.name}" assigned to {class_obj.name}!'
                )
                url = reverse('classes:class_detail', kwargs={'pk': class_pk})
                return redirect(f'{url}?tab=subjects')
    else:
        form = ClassSubjectForm(class_obj=class_obj)

    # Choose template based on request type
    template = 'classes/partials/class_subject_form_modal.html' if is_htmx else 'classes/class_subject_form.html'

    return render(request, template, {
        'form': form,
        'class': class_obj,
        'action': 'Assign'
    })


@school_admin_required
@require_http_methods(["DELETE"])
def class_subject_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Remove a subject from a class"""
    class_subject = get_object_or_404(ClassSubject, pk=pk)
    class_subject.is_active = False
    class_subject.save()
    
    return HttpResponse(headers={'HX-Trigger': 'classSubjectDeleted'})


# ============ Student Enrollment Views ============

@school_admin_required
def enrollment_create(request: HttpRequest, class_pk: int) -> HttpResponse:
    """Enroll a student in a class"""
    class_obj = get_object_or_404(Class, pk=class_pk)

    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST, class_obj=class_obj)
        if form.is_valid():
            # Check if class is full
            if class_obj.is_full():
                messages.error(
                    request,
                    f'{class_obj.name} is at full capacity ({class_obj.capacity} students).'
                )
                return render(request, 'classes/enrollment_form.html', {
                    'form': form,
                    'class': class_obj,
                    'action': 'Enroll'
                })

            enrollment = form.save(commit=False)
            enrollment.class_obj = class_obj
            enrollment.academic_year = class_obj.academic_year
            enrollment.status = StudentEnrollment.EnrollmentStatus.ENROLLED
            enrollment.final_result = StudentEnrollment.FinalResult.PENDING
            enrollment.is_active = True
            enrollment.save()
            messages.success(
                request,
                f'{enrollment.student.get_full_name()} enrolled in {class_obj.name}!'
            )
            return redirect('classes:class_detail', pk=class_pk)
    else:
        form = StudentEnrollmentForm(class_obj=class_obj)

    return render(request, 'classes/enrollment_form.html', {
        'form': form,
        'class': class_obj,
        'action': 'Enroll'
    })


@school_admin_required
@require_http_methods(["DELETE"])
def enrollment_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Remove a student from a class"""
    enrollment = get_object_or_404(StudentEnrollment, pk=pk)
    enrollment.is_active = False
    enrollment.save()

    return HttpResponse(headers={'HX-Trigger': 'enrollmentDeleted'})


@school_admin_required
def enrollment_bulk(request: HttpRequest, class_pk: int) -> HttpResponse:
    """Bulk enroll students in a class"""
    from students.models import Student
    from django.db.models import Exists, OuterRef
    from datetime import date

    class_obj = get_object_or_404(Class, pk=class_pk)
    is_htmx = request.headers.get('HX-Request') == 'true'

    # Check if class has academic year set
    if not class_obj.academic_year:
        messages.error(request, 'Cannot enroll students: This class does not have an academic year assigned. Please set the academic year first.')
        return redirect('classes:class_detail', class_pk)

    # Get currently enrolled students in THIS class
    enrolled_in_this_class = class_obj.enrollments.filter(is_active=True).values_list('student_id', flat=True)

    # Get all active students not enrolled in THIS class
    available_students = Student.objects.filter(
        is_active=True
    ).exclude(
        id__in=enrolled_in_this_class
    ).annotate(
        enrolled_elsewhere=Exists(
            StudentEnrollment.objects.filter(
                student=OuterRef('pk'),
                is_active=True
            ).exclude(class_obj=class_obj)
        )
    )

    # Apply search filter - check both GET and POST for HTMX requests
    search = request.POST.get('search_filter', '') or request.GET.get('search', '')
    grade_filter = request.POST.get('grade_filter', '') or request.GET.get('grade', '')

    if search:
        available_students = available_students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_id__icontains=search)
        )

    # Apply grade filter
    if grade_filter:
        # Filter students by their current enrollment's grade level
        available_students = available_students.filter(
            enrollments__is_active=True,
            enrollments__class_obj__grade_level=grade_filter
        ).distinct()

    # Order by name (can't order by grade since it's from enrollment)
    available_students = available_students.order_by('last_name', 'first_name')

    # Get all grades for filter dropdown
    all_grades = Class.GradeLevel.choices

    if request.method == 'POST' and not request.POST.get('search_filter') and not request.POST.get('grade_filter'):
        # Only process enrollment if not a filter request
        selected_student_ids = request.POST.getlist('students')
        enrollment_date = request.POST.get('enrollment_date', date.today())

        if not selected_student_ids:
            error_msg = 'Please select at least one student to enroll.'
            if is_htmx:
                return HttpResponse(
                    f'<div class="alert alert-error text-sm">'
                    f'<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">'
                    f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />'
                    f'</svg>'
                    f'<span>{error_msg}</span>'
                    f'</div>'
                )
            messages.error(request, error_msg)
            template = 'classes/partials/enrollment_bulk_modal.html' if is_htmx else 'classes/enrollment_bulk.html'
            return render(request, template, {
                'class': class_obj,
                'students': available_students,
                'enrollment_date': enrollment_date,
                'search': search,
                'grade_filter': grade_filter,
                'all_grades': all_grades,
            })

        # Check if class will exceed capacity
        current_count = class_obj.get_student_count()
        new_count = current_count + len(selected_student_ids)

        if new_count > class_obj.capacity:
            error_msg = (
                f'Cannot enroll {len(selected_student_ids)} students. '
                f'Class capacity: {class_obj.capacity}, Current: {current_count}, '
                f'Available slots: {class_obj.get_available_capacity()}'
            )
            if is_htmx:
                return HttpResponse(
                    f'<div class="alert alert-error text-sm">'
                    f'<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">'
                    f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />'
                    f'</svg>'
                    f'<span>{error_msg}</span>'
                    f'</div>'
                )
            messages.error(request, error_msg)
            template = 'classes/partials/enrollment_bulk_modal.html' if is_htmx else 'classes/enrollment_bulk.html'
            return render(request, template, {
                'class': class_obj,
                'students': available_students,
                'enrollment_date': enrollment_date,
                'search': search,
                'grade_filter': grade_filter,
                'all_grades': all_grades,
            })

        # Enroll selected students using bulk_create for efficiency
        from students.models import Student

        # Convert to integers for lookup
        selected_student_ids = [int(sid) for sid in selected_student_ids]

        # Fetch all students at once
        students = Student.objects.filter(id__in=selected_student_ids)
        student_dict = {s.id: s for s in students}

        # Bulk check existing enrollments
        existing_enrollments = set(
            StudentEnrollment.objects.filter(
                student_id__in=selected_student_ids,
                academic_year=class_obj.academic_year,
                is_active=True
            ).values_list('student_id', flat=True)
        )

        # Prepare bulk insert
        enrollments_to_create = []
        for student_id in selected_student_ids:
            if student_id not in existing_enrollments:
                enrollments_to_create.append(
                    StudentEnrollment(
                        student=student_dict[student_id],
                        class_obj=class_obj,
                        academic_year=class_obj.academic_year,
                        enrollment_date=enrollment_date,
                        status=StudentEnrollment.EnrollmentStatus.ENROLLED,
                        final_result=StudentEnrollment.FinalResult.PENDING,
                        is_active=True
                    )
                )

        # Single bulk insert
        StudentEnrollment.objects.bulk_create(enrollments_to_create)
        enrolled_count = len(enrollments_to_create)

        if enrolled_count > 0:
            success_msg = f'Successfully enrolled {enrolled_count} student(s) in {class_obj.name}!'
            if is_htmx:
                response = HttpResponse(
                    f'<div class="alert alert-success">'
                    f'<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">'
                    f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />'
                    f'</svg>'
                    f'<span>{success_msg}</span>'
                    f'</div>'
                )
                response['HX-Trigger'] = 'closeModal, reload'
                return response
            messages.success(request, success_msg)

        return redirect('classes:class_detail', pk=class_pk)

    # Choose template based on request type
    template = 'classes/partials/enrollment_bulk_modal.html' if is_htmx else 'classes/enrollment_bulk.html'

    return render(request, template, {
        'class': class_obj,
        'students': available_students,
        'enrollment_date': date.today(),
        'search': search,
        'grade_filter': grade_filter,
        'all_grades': all_grades,
    })


# ============ Promotion/Academic Year Management ============

@school_admin_required
def class_promote(request: HttpRequest, class_pk: int) -> HttpResponse:
    """Promote entire class to next grade level"""
    from datetime import date

    current_class = get_object_or_404(Class, pk=class_pk)

    # Get active enrollments for this class
    enrollments = current_class.enrollments.filter(
        is_active=True,
        status=StudentEnrollment.EnrollmentStatus.ENROLLED
    ).select_related('student')

    # Get available classes for next academic year (for selection)
    next_year_classes = Class.objects.filter(is_active=True).exclude(
        academic_year=current_class.academic_year
    ).order_by('grade_level', 'section')

    # Smart suggestion: Find the logical next grade class
    suggested_class = None
    current_grade = current_class.grade_level

    # Determine next grade level based on Ghana education structure
    grade_progression = {
        'Basic 1': 'Basic 2', 'Basic 2': 'Basic 3', 'Basic 3': 'Basic 4',
        'Basic 4': 'Basic 5', 'Basic 5': 'Basic 6', 'Basic 6': 'Basic 7',
        'Basic 7': 'Basic 8', 'Basic 8': 'Basic 9', 'Basic 9': 'SHS 1',
        'SHS 1': 'SHS 2', 'SHS 2': 'SHS 3'
    }

    next_grade = grade_progression.get(current_grade)
    if next_grade:
        # Try to find a matching class with same section/programme in next academic year
        suggested_class = next_year_classes.filter(
            grade_level=next_grade,
            section=current_class.section,
            programme=current_class.programme
        ).first()

        # If no exact match, try without section
        if not suggested_class:
            suggested_class = next_year_classes.filter(
                grade_level=next_grade,
                programme=current_class.programme
            ).first()

        # If still no match, try just by grade level
        if not suggested_class:
            suggested_class = next_year_classes.filter(grade_level=next_grade).first()

    if request.method == 'POST':
        next_class_id = request.POST.get('next_class')
        # Use academic year's end date as completion date
        completion_date = current_class.academic_year.end_date if current_class.academic_year else date.today()
        selected_student_ids = request.POST.getlist('selected_students')  # Get selected student IDs
        student_results = request.POST.dict()  # Get all form data

        if not next_class_id:
            messages.error(request, 'Please select a class for promotion.')
            return render(request, 'classes/class_promote.html', {
                'current_class': current_class,
                'enrollments': enrollments,
                'next_year_classes': next_year_classes,
                'suggested_class': suggested_class,
            })

        if not selected_student_ids:
            messages.error(request, 'Please select at least one student to process.')
            return render(request, 'classes/class_promote.html', {
                'current_class': current_class,
                'enrollments': enrollments,
                'next_year_classes': next_year_classes,
                'suggested_class': suggested_class,
            })

        next_class = get_object_or_404(Class, pk=next_class_id)

        # Convert selected IDs to integers for comparison
        selected_student_ids = [int(id) for id in selected_student_ids]

        # Process only selected students
        promoted_count = 0
        repeated_count = 0
        graduated_count = 0
        withdrawn_count = 0
        transferred_count = 0
        errors = []

        for enrollment in enrollments:
            # Skip if student is not selected
            if enrollment.student.id not in selected_student_ids:
                continue
            # Get individual student result from form
            result_key = f'result_{enrollment.student.id}'
            result = student_results.get(result_key, 'promoted')

            # Complete current enrollment
            enrollment.complete_enrollment(
                completion_date=completion_date,
                final_result=result
            )

            # Create new enrollment based on result
            if result == StudentEnrollment.FinalResult.PROMOTED:
                # Check capacity before creating enrollment
                if next_class.has_capacity():
                    StudentEnrollment.objects.create(
                        student=enrollment.student,
                        class_obj=next_class,
                        academic_year=next_class.academic_year,
                        enrollment_date=completion_date,
                        status=StudentEnrollment.EnrollmentStatus.ENROLLED,
                        final_result=StudentEnrollment.FinalResult.PENDING,
                        is_active=True
                    )
                    promoted_count += 1
                else:
                    errors.append(f"{enrollment.student.get_full_name()}: Target class is at capacity")

            elif result == StudentEnrollment.FinalResult.REPEATED:
                # Find same grade level class for next year
                repeated_class = Class.objects.filter(
                    grade_level=current_class.grade_level,
                    academic_year=next_class.academic_year,
                    is_active=True
                ).first()

                if repeated_class:
                    if repeated_class.has_capacity():
                        StudentEnrollment.objects.create(
                            student=enrollment.student,
                            class_obj=repeated_class,
                            academic_year=repeated_class.academic_year,
                            enrollment_date=completion_date,
                            status=StudentEnrollment.EnrollmentStatus.ENROLLED,
                            final_result=StudentEnrollment.FinalResult.PENDING,
                            is_active=True
                        )
                        repeated_count += 1
                    else:
                        errors.append(f"{enrollment.student.get_full_name()}: Repeated class is at capacity")
                else:
                    errors.append(f"{enrollment.student.get_full_name()}: No class found for repeating")

            elif result == StudentEnrollment.FinalResult.GRADUATED:
                # Student graduated - no new enrollment needed
                graduated_count += 1

            elif result == StudentEnrollment.FinalResult.WITHDRAWN:
                # Student withdrawn - no new enrollment needed
                withdrawn_count += 1

            elif result == StudentEnrollment.FinalResult.TRANSFERRED:
                # Student transferred - no new enrollment needed
                transferred_count += 1

        # Build success message
        summary_parts = []
        if promoted_count > 0:
            summary_parts.append(f"{promoted_count} promoted")
        if repeated_count > 0:
            summary_parts.append(f"{repeated_count} repeated")
        if graduated_count > 0:
            summary_parts.append(f"{graduated_count} graduated")
        if withdrawn_count > 0:
            summary_parts.append(f"{withdrawn_count} withdrawn")
        if transferred_count > 0:
            summary_parts.append(f"{transferred_count} transferred")

        if summary_parts:
            messages.success(request, f"Class promotion complete! {', '.join(summary_parts)}")

        # Show errors if any
        if errors:
            for error in errors:
                messages.warning(request, error)

        return redirect('classes:class_list')

    return render(request, 'classes/class_promote.html', {
        'current_class': current_class,
        'enrollments': enrollments,
        'next_year_classes': next_year_classes,
        'suggested_class': suggested_class,
    })


@school_admin_required
def student_transcript(request: HttpRequest, student_pk: int) -> HttpResponse:
    """View student's complete enrollment history (transcript)"""
    from students.models import Student

    student = get_object_or_404(Student, pk=student_pk)

    # Get all enrollments ordered by academic year
    enrollments = student.enrollments.all().select_related(
        'class_obj'
    ).order_by('-academic_year')

    # Get current enrollment
    current_enrollment = student.enrollments.filter(is_active=True).first()

    return render(request, 'classes/student_transcript.html', {
        'student': student,
        'enrollments': enrollments,
        'current_enrollment': current_enrollment,
    })


@school_admin_required
def student_transcript_pdf(request: HttpRequest, student_pk: int) -> HttpResponse:
    """Generate and download PDF of student transcript"""
    from students.models import Student

    student = get_object_or_404(Student, pk=student_pk)

    # Get all enrollments ordered by academic year
    enrollments = student.enrollments.all().select_related(
        'class_obj'
    ).order_by('-academic_year')

    # Get current enrollment
    current_enrollment = student.enrollments.filter(is_active=True).first()

    # Render the HTML template for PDF
    html_string = render_to_string('classes/student_transcript_pdf.html', {
        'student': student,
        'enrollments': enrollments,
        'current_enrollment': current_enrollment,
    }, request=request)

    # Create PDF
    font_config = FontConfiguration()
    html = HTML(string=html_string, base_url=request.build_absolute_uri())

    # Generate PDF with custom CSS
    pdf_css = CSS(string='''
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #2563eb;
            font-size: 24pt;
            margin-bottom: 10pt;
            border-bottom: 2pt solid #2563eb;
            padding-bottom: 5pt;
            text-align: center;
        }
        h2 {
            color: #1e40af;
            font-size: 16pt;
            margin-top: 15pt;
            margin-bottom: 8pt;
            border-bottom: 1pt solid #ddd;
            padding-bottom: 3pt;
        }
        .header-section {
            margin-bottom: 20pt;
            padding-bottom: 15pt;
            border-bottom: 2pt solid #e5e7eb;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10pt;
            margin-bottom: 20pt;
        }
        .stat-card {
            background: #f3f4f6;
            padding: 10pt;
            border-left: 3pt solid #2563eb;
        }
        .stat-label {
            font-size: 9pt;
            color: #666;
            text-transform: uppercase;
        }
        .stat-value {
            font-size: 16pt;
            font-weight: bold;
            color: #1e40af;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15pt;
            margin-bottom: 20pt;
        }
        .info-card {
            background: #f9fafb;
            padding: 10pt;
            border-left: 3pt solid #7c3aed;
        }
        .info-item {
            margin-bottom: 8pt;
        }
        .info-label {
            font-weight: bold;
            color: #666;
            font-size: 9pt;
            text-transform: uppercase;
        }
        .info-value {
            font-size: 11pt;
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10pt;
        }
        th {
            background-color: #7c3aed;
            color: white;
            padding: 8pt;
            text-align: left;
            font-weight: bold;
            font-size: 10pt;
        }
        td {
            padding: 6pt 8pt;
            border-bottom: 1pt solid #ddd;
            font-size: 10pt;
        }
        tr:nth-child(even) {
            background-color: #f9fafb;
        }
        tr.active-enrollment {
            background-color: #d1fae5 !important;
            border-left: 3pt solid #10b981;
        }
        .badge {
            display: inline-block;
            padding: 2pt 6pt;
            border-radius: 3pt;
            font-size: 8pt;
            font-weight: bold;
        }
        .badge-success { background: #d1fae5; color: #065f46; }
        .badge-info { background: #dbeafe; color: #1e40af; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .badge-error { background: #fee2e2; color: #991b1b; }
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10pt;
            margin-top: 15pt;
        }
        .summary-card {
            background: #f3f4f6;
            padding: 10pt;
            text-align: center;
            border-top: 3pt solid #2563eb;
        }
    ''', font_config=font_config)

    pdf = html.write_pdf(stylesheets=[pdf_css], font_config=font_config)

    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transcript_{student.student_id}_{student.get_full_name().replace(" ", "_")}.pdf"'

    return response


# ============ House Management Views ============

@school_admin_required
def house_list(request: HttpRequest) -> HttpResponse:
    """List all houses"""
    houses = House.objects.select_related('house_master').annotate(
        student_count=Count('students', filter=Q(students__is_active=True))
    )

    # Status filter
    status = request.GET.get('status', 'active')
    if status == 'active':
        houses = houses.filter(is_active=True)
    elif status == 'inactive':
        houses = houses.filter(is_active=False)

    # Search
    search = request.GET.get('search', '')
    if search:
        houses = houses.filter(
            Q(name__icontains=search) | Q(motto__icontains=search)
        )

    context = {
        'houses': houses,
        'search': search,
        'status': status,
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/house_list_content.html', context)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/house_list.html', context)


@school_admin_required
def house_create(request: HttpRequest) -> HttpResponse:
    """Create a new house"""
    if request.method == 'POST':
        form = HouseForm(request.POST)
        if form.is_valid():
            house = form.save()
            messages.success(request, f'House "{house.name}" created successfully!')
            return redirect('classes:house_list')
    else:
        form = HouseForm()

    context = {
        'form': form,
        'action': 'Create'
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/house_form_content.html', context)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/house_form.html', context)


@school_admin_required
def house_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View house details with students"""
    house = get_object_or_404(
        House.objects.select_related('house_master'),
        pk=pk
    )

    # Get students in this house
    students = house.students.filter(is_active=True).select_related('house')

    context = {
        'house': house,
        'students': students,
        'student_count': students.count(),
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/house_detail_content.html', context)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/house_detail.html', context)


@school_admin_required
def house_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a house"""
    house = get_object_or_404(House, pk=pk)

    if request.method == 'POST':
        form = HouseForm(request.POST, instance=house)
        if form.is_valid():
            house = form.save()
            messages.success(request, f'House "{house.name}" updated successfully!')
            return redirect('classes:house_detail', pk=house.pk)
    else:
        form = HouseForm(instance=house)

    context = {
        'form': form,
        'house': house,
        'action': 'Edit'
    }

    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        response = render(request, 'classes/partials/house_form_content.html', context)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    return render(request, 'classes/house_form.html', context)


@school_admin_required
@require_http_methods(["DELETE"])
def house_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft delete a house"""
    house = get_object_or_404(House, pk=pk)
    house.is_active = False
    house.save()

    return HttpResponse(headers={'HX-Trigger': 'houseDeleted'})
