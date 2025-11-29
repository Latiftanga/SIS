from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.db.models import Count, Q, Avg
from datetime import date, timedelta
from classes.models import Class, StudentEnrollment
from students.models import Student
from accounts.decorators import school_admin_required
from .models import AttendanceSession, AttendanceRecord
from .forms import AttendanceSessionForm, BulkAttendanceForm


@school_admin_required
def attendance_dashboard(request: HttpRequest) -> HttpResponse:
    """Attendance overview dashboard"""
    today = date.today()

    # Recent sessions
    recent_sessions = AttendanceSession.objects.all().select_related(
        'class_obj', 'subject'
    )[:10]

    # Today's stats
    today_sessions = AttendanceSession.objects.filter(date=today)
    total_today = today_sessions.count()

    # Classes with attendance marked today
    classes_marked_today = today_sessions.values_list('class_obj__name', flat=True).distinct()

    return render(request, 'attendance/dashboard.html', {
        'recent_sessions': recent_sessions,
        'total_today': total_today,
        'classes_marked_today': classes_marked_today,
        'today': today,
    })


@school_admin_required
def session_list(request: HttpRequest) -> HttpResponse:
    """List all attendance sessions with filtering"""
    sessions = AttendanceSession.objects.all().select_related(
        'class_obj', 'subject', 'marked_by'
    ).prefetch_related('records')

    # Filters
    class_filter = request.GET.get('class', '')
    if class_filter:
        sessions = sessions.filter(class_obj_id=class_filter)

    date_from = request.GET.get('date_from', '')
    if date_from:
        sessions = sessions.filter(date__gte=date_from)

    date_to = request.GET.get('date_to', '')
    if date_to:
        sessions = sessions.filter(date__lte=date_to)

    session_type = request.GET.get('type', '')
    if session_type:
        sessions = sessions.filter(session_type=session_type)

    # Get all classes for filter dropdown
    all_classes = Class.objects.filter(is_active=True).order_by('name')

    return render(request, 'attendance/session_list.html', {
        'sessions': sessions,
        'all_classes': all_classes,
        'class_filter': class_filter,
        'date_from': date_from,
        'date_to': date_to,
        'session_type': session_type,
    })


@school_admin_required
def session_create(request: HttpRequest, class_pk: int) -> HttpResponse:
    """Create a new attendance session for a class"""
    class_obj = get_object_or_404(Class, pk=class_pk)

    if request.method == 'POST':
        form = AttendanceSessionForm(request.POST, class_obj=class_obj)
        if form.is_valid():
            session = form.save(commit=False)
            session.class_obj = class_obj

            # Set marked_by if user is a teacher
            if hasattr(request.user, 'teacher'):
                session.marked_by = request.user.teacher

            session.save()
            messages.success(request, 'Attendance session created successfully!')
            return redirect('attendance:mark_attendance', session_pk=session.pk)
    else:
        form = AttendanceSessionForm(class_obj=class_obj, initial={'date': date.today()})

    return render(request, 'attendance/session_form.html', {
        'form': form,
        'class': class_obj,
        'action': 'Create',
    })


@school_admin_required
def mark_attendance(request: HttpRequest, session_pk: int) -> HttpResponse:
    """Mark attendance for students in a session"""
    session = get_object_or_404(
        AttendanceSession.objects.select_related('class_obj', 'subject'),
        pk=session_pk
    )

    # Check if session is finalized
    if session.is_finalized:
        messages.warning(request, 'This attendance session is finalized and cannot be edited.')
        return redirect('attendance:session_detail', session_pk=session.pk)

    # Get active enrollments for this class
    enrollments = StudentEnrollment.objects.filter(
        class_obj=session.class_obj,
        is_active=True,
        status=StudentEnrollment.EnrollmentStatus.ENROLLED
    ).select_related('student').order_by('roll_number', 'student__last_name', 'student__first_name')

    students = [enrollment.student for enrollment in enrollments]

    # Get existing attendance records
    existing_records = {
        record.student_id: record
        for record in session.records.all()
    }

    # Attach existing records to enrollments for easier template access
    enrollments_list = list(enrollments)
    for enrollment in enrollments_list:
        enrollment.existing_record = existing_records.get(enrollment.student_id)

    if request.method == 'POST':
        form = BulkAttendanceForm(
            request.POST,
            students=students,
            existing_records=existing_records
        )

        if form.is_valid():
            # Process each student's attendance
            for enrollment in enrollments:
                student = enrollment.student
                status = form.cleaned_data.get(f'status_{student.id}')
                time_in = form.cleaned_data.get(f'time_in_{student.id}')
                remarks = form.cleaned_data.get(f'remarks_{student.id}')

                # Update or create attendance record
                record, created = AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={
                        'enrollment': enrollment,
                        'status': status,
                        'time_in': time_in if status == AttendanceRecord.Status.LATE else None,
                        'remarks': remarks,
                    }
                )

            # Check if user wants to finalize
            if 'finalize' in request.POST:
                session.is_finalized = True
                session.save()
                messages.success(
                    request,
                    f'Attendance marked and finalized for {session.class_obj.name} on {session.date}!'
                )
            else:
                messages.success(
                    request,
                    f'Attendance saved for {session.class_obj.name} on {session.date}!'
                )

            return redirect('attendance:session_detail', session_pk=session.pk)
    else:
        form = BulkAttendanceForm(
            students=students,
            existing_records=existing_records
        )

    return render(request, 'attendance/mark_attendance.html', {
        'session': session,
        'form': form,
        'students': students,
        'enrollments': enrollments_list,
        'existing_records': existing_records,
    })


@school_admin_required
def session_detail(request: HttpRequest, session_pk: int) -> HttpResponse:
    """View attendance session details"""
    session = get_object_or_404(
        AttendanceSession.objects.select_related('class_obj', 'subject', 'marked_by'),
        pk=session_pk
    )

    records = session.records.all().select_related('student', 'enrollment').order_by(
        'enrollment__roll_number', 'student__last_name', 'student__first_name'
    )

    return render(request, 'attendance/session_detail.html', {
        'session': session,
        'records': records,
    })


@school_admin_required
def student_attendance_report(request: HttpRequest, student_pk: int) -> HttpResponse:
    """View individual student's attendance report"""
    student = get_object_or_404(Student, pk=student_pk)

    # Get current enrollment
    current_enrollment = student.enrollments.filter(is_active=True).first()

    # Get all attendance records
    records = AttendanceRecord.objects.filter(
        student=student
    ).select_related('session', 'session__class_obj').order_by('-session__date')

    # Calculate statistics
    total_sessions = records.count()
    present_count = records.filter(status=AttendanceRecord.Status.PRESENT).count()
    absent_count = records.filter(status=AttendanceRecord.Status.ABSENT).count()
    late_count = records.filter(status=AttendanceRecord.Status.LATE).count()
    excused_count = records.filter(status=AttendanceRecord.Status.EXCUSED).count()

    attendance_rate = round((present_count + late_count) / total_sessions * 100, 2) if total_sessions > 0 else 0

    return render(request, 'attendance/student_report.html', {
        'student': student,
        'current_enrollment': current_enrollment,
        'records': records,
        'total_sessions': total_sessions,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'excused_count': excused_count,
        'attendance_rate': attendance_rate,
    })


@school_admin_required
def class_attendance_report(request: HttpRequest, class_pk: int) -> HttpResponse:
    """View class-wide attendance report"""
    class_obj = get_object_or_404(Class, pk=class_pk)

    # Get date range from filters or default to current month
    date_from = request.GET.get('date_from', date.today().replace(day=1).isoformat())
    date_to = request.GET.get('date_to', date.today().isoformat())

    # Get sessions in date range
    sessions = AttendanceSession.objects.filter(
        class_obj=class_obj,
        date__gte=date_from,
        date__lte=date_to
    ).order_by('-date')

    # Get active enrollments
    enrollments = StudentEnrollment.objects.filter(
        class_obj=class_obj,
        is_active=True
    ).select_related('student').order_by('roll_number', 'student__last_name', 'student__first_name')

    # Calculate attendance stats for each student
    student_stats = []
    for enrollment in enrollments:
        student = enrollment.student
        student_records = AttendanceRecord.objects.filter(
            student=student,
            session__in=sessions
        )

        total = student_records.count()
        present = student_records.filter(status=AttendanceRecord.Status.PRESENT).count()
        late = student_records.filter(status=AttendanceRecord.Status.LATE).count()
        absent = student_records.filter(status=AttendanceRecord.Status.ABSENT).count()

        rate = round((present + late) / total * 100, 2) if total > 0 else 0

        student_stats.append({
            'student': student,
            'roll_number': enrollment.roll_number,
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'rate': rate,
        })

    return render(request, 'attendance/class_report.html', {
        'class': class_obj,
        'sessions': sessions,
        'student_stats': student_stats,
        'date_from': date_from,
        'date_to': date_to,
    })


@school_admin_required
def session_delete(request: HttpRequest, session_pk: int) -> HttpResponse:
    """Delete an attendance session"""
    session = get_object_or_404(AttendanceSession, pk=session_pk)

    if session.is_finalized:
        messages.error(request, 'Cannot delete a finalized attendance session.')
        return redirect('attendance:session_detail', session_pk=session.pk)

    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Attendance session deleted successfully!')
        return redirect('attendance:session_list')

    return render(request, 'attendance/session_confirm_delete.html', {
        'session': session,
    })
