from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, HttpResponse
from django.db.models import Q, Count
from .models import Subject, Class, ClassSubject, StudentEnrollment
from .forms import (
    SubjectForm, ClassForm, ClassSubjectForm, 
    StudentEnrollmentForm, BulkEnrollmentForm
)
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
    
    return render(request, 'classes/subject_form.html', {
        'form': form,
        'action': 'Create'
    })


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
    
    return render(request, 'classes/subject_form.html', {
        'form': form,
        'subject': subject,
        'action': 'Edit'
    })


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
    classes = Class.objects.select_related('class_teacher').annotate(
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
    
    return render(request, 'classes/class_list.html', context)


@school_admin_required
def class_create(request: HttpRequest) -> HttpResponse:
    """Create a new class"""
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class "{class_obj.name}" created successfully!')
            return redirect('classes:class_list')
    else:
        form = ClassForm()
    
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
    
    return render(request, 'classes/class_detail.html', context)


@school_admin_required
def class_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit a class"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            class_obj = form.save()
            messages.success(request, f'Class "{class_obj.name}" updated successfully!')
            return redirect('classes:class_detail', pk=class_obj.pk)
    else:
        form = ClassForm(instance=class_obj)
    
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
    class_obj = get_object_or_404(Class, pk=class_pk)

    if request.method == 'POST':
        form = ClassSubjectForm(request.POST, class_obj=class_obj)
        if form.is_valid():
            class_subject = form.save(commit=False)
            class_subject.class_obj = class_obj  # Explicitly set the class
            class_subject.save()
            messages.success(
                request,
                f'Subject "{class_subject.subject.name}" assigned to {class_obj.name}!'
            )
            return redirect('classes:class_detail', pk=class_pk)
    else:
        form = ClassSubjectForm(class_obj=class_obj)

    return render(request, 'classes/class_subject_form.html', {
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

    # Apply filters
    grade_filter = request.GET.get('grade', '')
    if grade_filter:
        available_students = available_students.filter(current_grade=grade_filter)

    search = request.GET.get('search', '')
    if search:
        available_students = available_students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_id__icontains=search)
        )

    available_students = available_students.order_by('current_grade', 'last_name', 'first_name')

    # Get unique grades for filter dropdown
    all_grades = Student.objects.filter(
        is_active=True
    ).values_list('current_grade', flat=True).distinct().order_by('current_grade')

    if request.method == 'POST':
        selected_student_ids = request.POST.getlist('students')
        enrollment_date = request.POST.get('enrollment_date', date.today())

        if not selected_student_ids:
            messages.error(request, 'Please select at least one student to enroll.')
            return render(request, 'classes/enrollment_bulk.html', {
                'class': class_obj,
                'students': available_students,
                'enrollment_date': enrollment_date,
            })

        # Check if class will exceed capacity
        current_count = class_obj.get_student_count()
        new_count = current_count + len(selected_student_ids)

        if new_count > class_obj.capacity:
            messages.error(
                request,
                f'Cannot enroll {len(selected_student_ids)} students. '
                f'Class capacity: {class_obj.capacity}, Current: {current_count}, '
                f'Available slots: {class_obj.get_available_capacity()}'
            )
            return render(request, 'classes/enrollment_bulk.html', {
                'class': class_obj,
                'students': available_students,
                'enrollment_date': enrollment_date,
            })

        # Enroll selected students
        enrolled_count = 0
        for student_id in selected_student_ids:
            student = Student.objects.get(id=student_id)

            # Check if student is already enrolled for this academic year
            existing = StudentEnrollment.objects.filter(
                student=student,
                academic_year=class_obj.academic_year,
                is_active=True
            ).exists()

            if not existing:
                StudentEnrollment.objects.create(
                    student=student,
                    class_obj=class_obj,
                    academic_year=class_obj.academic_year,
                    enrollment_date=enrollment_date,
                    status=StudentEnrollment.EnrollmentStatus.ENROLLED,
                    final_result=StudentEnrollment.FinalResult.PENDING,
                    is_active=True
                )
                enrolled_count += 1

        if enrolled_count > 0:
            messages.success(
                request,
                f'Successfully enrolled {enrolled_count} student(s) in {class_obj.name}!'
            )

        return redirect('classes:class_detail', pk=class_pk)

    return render(request, 'classes/enrollment_bulk.html', {
        'class': class_obj,
        'students': available_students,
        'enrollment_date': date.today(),
        'all_grades': all_grades,
        'grade_filter': grade_filter,
        'search': search,
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

    if request.method == 'POST':
        next_class_id = request.POST.get('next_class')
        completion_date = request.POST.get('completion_date', date.today())
        student_results = request.POST.dict()  # Get all form data

        if not next_class_id:
            messages.error(request, 'Please select a class for promotion.')
            return render(request, 'classes/class_promote.html', {
                'current_class': current_class,
                'enrollments': enrollments,
                'next_year_classes': next_year_classes,
            })

        next_class = get_object_or_404(Class, pk=next_class_id)

        # Process each student
        promoted_count = 0
        repeated_count = 0

        for enrollment in enrollments:
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
            elif result == StudentEnrollment.FinalResult.REPEATED:
                # Find same grade level class for next year
                repeated_class = Class.objects.filter(
                    grade_level=current_class.grade_level,
                    academic_year=next_class.academic_year
                ).first()

                if repeated_class:
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

        messages.success(
            request,
            f'Class promotion complete! Promoted: {promoted_count}, Repeated: {repeated_count}'
        )
        return redirect('classes:class_list')

    return render(request, 'classes/class_promote.html', {
        'current_class': current_class,
        'enrollments': enrollments,
        'next_year_classes': next_year_classes,
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
