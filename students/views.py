# students/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from .models import Student, Programme
from .forms import StudentCreateForm, StudentBulkImportForm, ProgrammeForm
from accounts.models import User
from accounts.decorators import school_admin_required
from accounts.utils import generate_secure_password
from datetime import date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import csv
from io import BytesIO


@school_admin_required
def student_list(request: HttpRequest) -> HttpResponse:
    """List all students with HTMX support"""
    students = Student.objects.select_related('user').all()

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        students = students.filter(is_active=True)
    elif status == 'inactive':
        students = students.filter(is_active=False)
    else:
        # Default to showing only active students
        students = students.filter(is_active=True)

    # Gender filter
    gender = request.GET.get('gender', '')
    if gender:
        students = students.filter(gender=gender)

    # Grade filter
    grade = request.GET.get('grade', '')
    if grade:
        students = students.filter(current_grade=grade)

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_id__icontains=search) |
            Q(guardian_name__icontains=search)
        )

    # Get unique grades for filter dropdown
    grades = Student.objects.filter(is_active=True).values_list('current_grade', flat=True).distinct().order_by('current_grade')

    context = {
        'students': students,
        'search': search,
        'status': status,
        'gender': gender,
        'grade': grade,
        'grades': grades,
    }

    # If HTMX request for search/filters, return only the table rows
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'students-table':
        return render(request, 'students/partials/student_rows.html', context)

    # Full page render
    return render(request, 'students/student_list.html', context)


@school_admin_required
def student_create(request: HttpRequest) -> HttpResponse:
    """Show create student form or handle form submission"""
    if request.method == 'POST':
        form = StudentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save with request for email URL building
                student, generated_password = form.save(request=request)

                # Build success message
                success_message = f'Student {student.get_full_name()} added successfully!'
                if generated_password:
                    email = student.email or student.guardian_email
                    success_message += f' Credentials sent to {email}'

                messages.success(request, success_message)
                return redirect('students:list')
            except Exception as e:
                messages.error(request, f'Error creating student: {str(e)}')
    else:
        form = StudentCreateForm()

    return render(request, 'students/student_create.html', {'form': form})


@school_admin_required
def student_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View student details"""
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'students/student_detail_page.html', {
        'student': student
    })


@school_admin_required
@require_http_methods(["DELETE"])
def student_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft delete student"""
    student = get_object_or_404(Student, pk=pk)
    student.is_active = False
    student.save()

    # Return empty response to remove the row
    return HttpResponse(headers={'HX-Trigger': 'studentDeleted'})


@school_admin_required
@require_http_methods(["GET", "POST"])
def student_bulk_import(request: HttpRequest) -> HttpResponse:
    """
    Bulk import students from Excel or CSV file.
    Shows upload form and preview of data to be imported.
    """
    if request.method == 'POST':
        form = StudentBulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Parse file
                students_data = form.parse_file()
                create_accounts = form.cleaned_data['create_user_accounts']

                # Store data in session for processing
                request.session['bulk_import_data'] = students_data
                request.session['bulk_import_create_accounts'] = create_accounts

                # Calculate statistics
                valid_count = sum(1 for s in students_data if s['valid'])
                invalid_count = len(students_data) - valid_count

                context = {
                    'students': students_data,
                    'total': len(students_data),
                    'valid': valid_count,
                    'invalid': invalid_count,
                    'create_accounts': create_accounts,
                }

                return render(request, 'students/bulk_import_preview.html', context)

            except Exception as e:
                messages.error(request, f'Error parsing file: {str(e)}')
    else:
        form = StudentBulkImportForm()

    return render(request, 'students/bulk_import.html', {'form': form})


@school_admin_required
@require_http_methods(["POST"])
def student_bulk_import_process(request: HttpRequest) -> HttpResponse:
    """
    Process bulk import after preview confirmation.
    Creates student records and optionally user accounts.
    """
    students_data = request.session.get('bulk_import_data', [])
    create_accounts = request.session.get('bulk_import_create_accounts', False)

    if not students_data:
        messages.error(request, 'No import data found. Please upload a file first.')
        return redirect('students:bulk_import')

    success_count = 0
    error_count = 0
    errors = []

    for student_data in students_data:
        # Skip invalid rows
        if not student_data['valid']:
            error_count += 1
            continue

        try:
            # Create student
            student = Student(
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                other_names=student_data.get('other_names', ''),
                email=student_data.get('email', ''),
                gender=student_data['gender'],
                phone_number=student_data.get('phone_number', ''),
                residential_address=student_data.get('residential_address', ''),
                student_id=student_data['student_id'],
                admission_date=student_data['admission_date'],
                date_of_birth=student_data['date_of_birth'],
                current_grade=student_data['current_grade'],
                guardian_name=student_data['guardian_name'],
                guardian_relationship=student_data.get('guardian_relationship', 'Parent'),
                guardian_phone=student_data['guardian_phone'],
                guardian_email=student_data.get('guardian_email', ''),
                guardian_address=student_data.get('guardian_address', ''),
                emergency_contact_name=student_data.get('emergency_contact_name', ''),
                emergency_contact_phone=student_data.get('emergency_contact_phone', ''),
                medical_conditions=student_data.get('medical_conditions', ''),
            )

            # Create user account if requested and student has email
            should_create_account = (create_accounts or student_data.get('create_account', False)) and student_data.get('email')
            if should_create_account:
                # Generate password
                password = generate_secure_password()

                # Create user
                user = User.objects.create_student(
                    email=student_data['email'],
                    password=password
                )
                user.force_password_change = True
                user.save()

                student.user = user

            student.save()
            success_count += 1

        except Exception as e:
            error_count += 1
            errors.append(f"Row {student_data['row_num']}: {str(e)}")

    # Clear session data
    if 'bulk_import_data' in request.session:
        del request.session['bulk_import_data']
    if 'bulk_import_create_accounts' in request.session:
        del request.session['bulk_import_create_accounts']

    # Show results
    if success_count > 0:
        messages.success(
            request,
            f'Successfully imported {success_count} student(s).'
        )

    if error_count > 0:
        error_msg = f'Failed to import {error_count} student(s).'
        if errors:
            error_msg += ' Errors: ' + '; '.join(errors[:5])
        messages.error(request, error_msg)

    return redirect('students:list')


@school_admin_required
def student_download_template(request: HttpRequest) -> HttpResponse:
    """
    Download sample Excel template for bulk import.
    """
    file_format = request.GET.get('format', 'xlsx')

    if file_format == 'csv':
        return _generate_csv_template()
    else:
        return _generate_excel_template()


def _generate_excel_template() -> HttpResponse:
    """Generate Excel template with sample data."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"

    # Define headers
    headers = [
        'first_name', 'last_name', 'other_names', 'date_of_birth',
        'gender', 'email', 'phone_number', 'residential_address',
        'student_id', 'admission_date', 'current_grade',
        'guardian_name', 'guardian_relationship', 'guardian_phone',
        'guardian_email', 'guardian_address',
        'emergency_contact_name', 'emergency_contact_phone',
        'medical_conditions', 'create_account'
    ]

    # Style headers
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Add sample data
    sample_data = [
        [
            'Kwame', 'Mensah', 'Kofi', '2010-03-15',
            'Male', 'kwame.mensah@example.com', '+233244123456', '123 Main St, Accra',
            'STU001', '2024-09-01', 'Grade 5',
            'Abena Mensah', 'Mother', '+233244987654',
            'abena.mensah@example.com', '123 Main St, Accra',
            'Yaw Mensah', '+233244111222',
            '', 'yes'
        ],
        [
            'Akua', 'Owusu', '', '2012-07-20',
            'Female', '', '0244567890', '456 Oak Ave, Kumasi',
            'STU002', '2024-09-01', 'Grade 3',
            'Kwesi Owusu', 'Father', '0244333444',
            'kwesi.owusu@example.com', '456 Oak Ave, Kumasi',
            '', '',
            'Asthma - requires inhaler', 'no'
        ],
    ]

    for row_num, row_data in enumerate(sample_data, 2):
        for col_num, value in enumerate(row_data, 1):
            ws.cell(row=row_num, column=col_num, value=value)

    # Auto-size columns
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Save to BytesIO buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Create response
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="students_import_template_{timezone.now().strftime("%Y%m%d")}.xlsx"'

    return response


def _generate_csv_template() -> HttpResponse:
    """Generate CSV template with sample data."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="students_import_template_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    # Write headers
    headers = [
        'first_name', 'last_name', 'other_names', 'date_of_birth',
        'gender', 'email', 'phone_number', 'residential_address',
        'student_id', 'admission_date', 'current_grade',
        'guardian_name', 'guardian_relationship', 'guardian_phone',
        'guardian_email', 'guardian_address',
        'emergency_contact_name', 'emergency_contact_phone',
        'medical_conditions', 'create_account'
    ]
    writer.writerow(headers)

    # Write sample data
    sample_data = [
        [
            'Kwame', 'Mensah', 'Kofi', '2010-03-15',
            'Male', 'kwame.mensah@example.com', '+233244123456', '123 Main St, Accra',
            'STU001', '2024-09-01', 'Grade 5',
            'Abena Mensah', 'Mother', '+233244987654',
            'abena.mensah@example.com', '123 Main St, Accra',
            'Yaw Mensah', '+233244111222',
            '', 'yes'
        ],
        [
            'Akua', 'Owusu', '', '2012-07-20',
            'Female', '', '0244567890', '456 Oak Ave, Kumasi',
            'STU002', '2024-09-01', 'Grade 3',
            'Kwesi Owusu', 'Father', '0244333444',
            'kwesi.owusu@example.com', '456 Oak Ave, Kumasi',
            '', '',
            'Asthma - requires inhaler', 'no'
        ],
    ]

    for row in sample_data:
        writer.writerow(row)

    return response


# ==================== Programme Views ====================


@school_admin_required
def programme_list(request: HttpRequest) -> HttpResponse:
    """List all programmes with HTMX support"""
    programmes = Programme.objects.all()

    # Status filter
    status = request.GET.get('status', '')
    if status == 'active':
        programmes = programmes.filter(is_active=True)
    elif status == 'inactive':
        programmes = programmes.filter(is_active=False)
    else:
        # Default to showing only active programmes
        programmes = programmes.filter(is_active=True)

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        programmes = programmes.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )

    context = {
        'programmes': programmes,
        'search': search,
        'status': status,
    }

    # If HTMX request for search/filters, return only the table rows
    if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'programmes-table':
        return render(request, 'students/programmes/partials/programme_rows.html', context)

    # Full page render
    return render(request, 'students/programmes/programme_list.html', context)


@school_admin_required
def programme_create(request: HttpRequest) -> HttpResponse:
    """Show create programme form or handle form submission"""
    if request.method == 'POST':
        form = ProgrammeForm(request.POST)
        if form.is_valid():
            try:
                programme = form.save()
                messages.success(request, f'Programme "{programme.name}" created successfully!')
                return redirect('students:programme_list')
            except Exception as e:
                messages.error(request, f'Error creating programme: {str(e)}')
    else:
        form = ProgrammeForm()

    return render(request, 'students/programmes/programme_form.html', {
        'form': form,
        'action': 'Create'
    })


@school_admin_required
def programme_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit existing programme"""
    programme = get_object_or_404(Programme, pk=pk)

    if request.method == 'POST':
        form = ProgrammeForm(request.POST, instance=programme)
        if form.is_valid():
            try:
                programme = form.save()
                messages.success(request, f'Programme "{programme.name}" updated successfully!')
                return redirect('students:programme_list')
            except Exception as e:
                messages.error(request, f'Error updating programme: {str(e)}')
    else:
        form = ProgrammeForm(instance=programme)

    return render(request, 'students/programmes/programme_form.html', {
        'form': form,
        'action': 'Edit',
        'programme': programme
    })


@school_admin_required
@require_http_methods(["DELETE"])
def programme_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Soft delete programme"""
    programme = get_object_or_404(Programme, pk=pk)
    programme.is_active = False
    programme.save()

    # Return empty response to remove the row
    return HttpResponse(headers={'HX-Trigger': 'programmeDeleted'})
