# teachers/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from .models import Teacher
from accounts.models import User
from datetime import date


@login_required
def teacher_list(request):
    """List all teachers with HTMX support"""
    teachers = Teacher.objects.select_related('user').filter(is_active=True)
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        teachers = teachers.filter(
            first_name__icontains=search
        ) | teachers.filter(
            last_name__icontains=search
        ) | teachers.filter(
            employee_id__icontains=search
        )
    
    # If HTMX request, return only the table rows
    if request.headers.get('HX-Request'):
        return render(request, 'teachers/partials/teacher_rows.html', {
            'teachers': teachers
        })
    
    # Full page render
    return render(request, 'teachers/teacher_list.html', {
        'teachers': teachers,
        'search': search
    })


@login_required
def teacher_create(request):
    """Show create teacher form"""
    if request.method == 'GET':
        return render(request, 'teachers/partials/teacher_form.html')
    
    # Handle form submission
    if request.method == 'POST':
        try:
            # Create user account
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            if User.objects.filter(email=email).exists():
                return HttpResponse(
                    '<div class="alert alert-error"><span>Email already exists!</span></div>',
                    status=400
                )
            
            user = User.objects.create_teacher(email=email, password=password)
            
            # Create teacher profile
            teacher = Teacher.objects.create(
                user=user,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                other_names=request.POST.get('other_names', ''),
                phone_number=request.POST.get('phone_number'),
                employee_id=request.POST.get('employee_id'),
                date_joined=request.POST.get('date_joined') or date.today(),
            )
            
            # Return success response with new row
            return render(request, 'teachers/partials/teacher_row.html', {
                'teacher': teacher
            }, headers={'HX-Trigger': 'teacherAdded'})
            
        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error"><span>Error: {str(e)}</span></div>',
                status=400
            )


@login_required
def teacher_detail(request, pk):
    """View teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    return render(request, 'teachers/partials/teacher_detail.html', {
        'teacher': teacher
    })


@login_required
@require_http_methods(["DELETE"])
def teacher_delete(request, pk):
    """Soft delete teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.is_active = False
    teacher.save()
    
    # Return empty response to remove the row
    return HttpResponse(headers={'HX-Trigger': 'teacherDeleted'})