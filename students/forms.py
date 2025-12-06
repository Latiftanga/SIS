from typing import Optional, Tuple, List, Dict, Any
from django import forms
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .models import Student, Programme
from accounts.utils import generate_secure_password
from core.models import SchoolSettings
import openpyxl
import csv
from io import TextIOWrapper
from datetime import datetime

User = get_user_model()


class StudentCreateForm(forms.ModelForm):
    """
    Form for creating a new student with optional user account.

    Best Practices Implemented:
    - Optional user account creation via checkbox
    - Auto-generated secure passwords
    - Email notifications with credentials
    - Force password change on first login
    """

    # Account Creation Option
    create_user_account = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary',
            'id': 'create_user_account_checkbox'
        }),
        label='Create user account for system access',
        help_text='Enable this to create a login account for the student'
    )

    # Class Enrollment Option
    class_enrollment = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full'
        }),
        label='Assign to Class',
        help_text='Optional: Assign student to a class'
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'other_names', 'date_of_birth', 'gender',
            'email', 'phone_number', 'residential_address',
            'student_id', 'admission_date',
            'guardian_name', 'guardian_relationship', 'guardian_phone',
            'guardian_email', 'guardian_address',
            'emergency_contact_name', 'emergency_contact_phone',
            'medical_conditions',
            'residence_status', 'dormitory', 'bed_number', 'house',
            'photo'
        ]
        widgets = {
            # Personal Information
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'First name',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Last name',
                'required': True
            }),
            'other_names': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Other names (optional)'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
                'required': True
            }),
            'gender': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            
            # Contact Information
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'email@example.com (optional)'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': '+233XXXXXXXXX or 0XXXXXXXXX (optional)'
            }),
            'residential_address': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Residential address (optional)'
            }),
            
            # Student Information
            'student_id': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Student ID',
                'required': True
            }),
            'admission_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
                'required': True
            }),

            # Guardian Information
            'guardian_name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Full name of parent/guardian',
                'required': True
            }),
            'guardian_relationship': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': '+233XXXXXXXXX or 0XXXXXXXXX',
                'required': True
            }),
            'guardian_email': forms.EmailInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'guardian@example.com (optional)'
            }),
            'guardian_address': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Guardian address (optional)'
            }),
            
            # Emergency Contact
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Emergency contact name (optional)'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': '+233XXXXXXXXX or 0XXXXXXXXX (optional)'
            }),
            
            # Medical
            'medical_conditions': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Any medical conditions, allergies, or special needs (optional)'
            }),

            # Boarding/Residence Information (for SHS students)
            'residence_status': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'dormitory': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Dormitory/Hostel name (for boarding students)'
            }),
            'bed_number': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Bed/Cubicle number (for boarding students)'
            }),
            'house': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),

            # Photo
            'photo': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered file-input-sm w-full',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form and set class queryset."""
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from classes.models import Class, StudentEnrollment, House

        # Set class queryset to active classes
        self.fields['class_enrollment'].queryset = Class.objects.filter(is_active=True).order_by('grade_level', 'section')

        # Set house queryset to active houses
        self.fields['house'].queryset = House.objects.filter(is_active=True)
        self.fields['house'].required = False

        # If editing existing student, pre-select their current class
        if self.instance.pk:
            try:
                # Get the most recent active enrollment
                current_enrollment = StudentEnrollment.objects.filter(
                    student=self.instance,
                    is_active=True
                ).order_by('-created_at').first()

                if current_enrollment:
                    self.fields['class_enrollment'].initial = current_enrollment.class_obj
            except StudentEnrollment.DoesNotExist:
                pass

    def clean_email(self) -> str:
        """Validate email uniqueness if provided and creating user account."""
        email = self.cleaned_data.get('email')
        create_user_account = self.data.get('create_user_account')
        
        if email:
            # Check if email already exists in Student model
            qs = Student.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A student with this email already exists.')
            
            # Check User model only if creating user account
            if create_user_account and User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    'A user account with this email already exists. '
                    'Uncheck "Create user account" if you only want to create a student profile.'
                )
        elif create_user_account:
            raise forms.ValidationError('Email is required when creating a user account.')
        
        return email

    def clean_student_id(self) -> str:
        """Validate that student_id is unique."""
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            qs = Student.objects.filter(student_id=student_id)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A student with this ID already exists.')
        return student_id

    def _create_user_account(self, email: str) -> Tuple[User, str]:
        """Create user account with auto-generated password."""
        password = generate_secure_password()
        user = User.objects.create_student(email=email, password=password)
        user.force_password_change = True
        user.save()
        return user, password

    def _send_welcome_email(
        self,
        student: Student,
        password: Optional[str] = None,
        request = None
    ) -> None:
        """Send welcome email to student (or guardian if student has no email)."""
        school_settings = SchoolSettings.get_settings()
        school_name = school_settings.short_name if school_settings else 'SmartSIS'
        
        # Determine recipient
        recipient_email = student.email if student.email else student.guardian_email
        if not recipient_email:
            return  # No email to send to
        
        # Build login URL
        if request:
            domain = get_current_site(request).domain
            protocol = 'https' if request.is_secure() else 'http'
            login_url = f"{protocol}://{domain}/accounts/login/"
        else:
            login_url = "http://localhost:8000/accounts/login/"
        
        # Prepare email context
        context = {
            'student_name': student.get_full_name(),
            'school_name': school_name,
            'user_account_created': student.user is not None,
            'email': student.email or student.guardian_email,
            'password': password,
            'login_url': login_url,
            'is_guardian': not student.email,
            'guardian_name': student.guardian_name if not student.email else None,
        }
        
        # Send email (use text for now, can create templates later)
        subject = f'Welcome to {school_name}!'
        if student.user:
            message = f"""
Hello {student.get_full_name()},

Welcome to {school_name}!

Your student account has been created with the following credentials:
Email: {student.email or student.guardian_email}
Password: {password}

Please log in at: {login_url}
You will be required to change your password on first login.

Best regards,
{school_name}
            """
        else:
            message = f"""
Hello,

Student {student.get_full_name()} has been enrolled at {school_name}.

Student ID: {student.student_id}
Grade: {student.get_current_grade()}

Best regards,
{school_name}
            """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[recipient_email],
            fail_silently=True,
        )

    def save(self, commit: bool = True, request = None) -> Tuple[Student, Optional[str]]:
        """Create student profile and optionally user account."""
        student = super().save(commit=False)
        user = None
        password = None

        # Create user account if checkbox is checked, student doesn't already have one, and email is provided
        if self.cleaned_data.get('create_user_account') and not student.user and student.email:
            user, password = self._create_user_account(student.email)
            student.user = user

        if commit:
            student.save()
            # Send welcome email only if password was generated (new account or new user)
            if password:
                self._send_welcome_email(student, password, request)

            # Handle class enrollment
            self._handle_class_enrollment(student)

        return student, password

    def _handle_class_enrollment(self, student: Student) -> None:
        """Handle class enrollment create/update/delete."""
        from classes.models import Class, StudentEnrollment
        from datetime import date

        # Get selected class
        selected_class = self.cleaned_data.get('class_enrollment')

        # Get existing active enrollment
        existing_enrollment = StudentEnrollment.objects.filter(
            student=student,
            is_active=True
        ).order_by('-created_at').first()

        if selected_class:
            # Determine academic year from selected class or use default
            academic_year = selected_class.academic_year if hasattr(selected_class, 'academic_year') and selected_class.academic_year else '2024/2025'

            # Create or update enrollment
            if existing_enrollment:
                # Update existing enrollment if class changed
                if existing_enrollment.class_obj != selected_class:
                    existing_enrollment.class_obj = selected_class
                    existing_enrollment.academic_year = academic_year
                    existing_enrollment.save()
            else:
                # Create new enrollment
                StudentEnrollment.objects.create(
                    student=student,
                    class_obj=selected_class,
                    academic_year=academic_year,
                    enrollment_date=student.admission_date or date.today(),
                    status='enrolled',
                    is_active=True
                )
        else:
            # No class selected - remove enrollment if exists
            if existing_enrollment:
                existing_enrollment.delete()


class StudentBulkImportForm(forms.Form):
    """
    Form for bulk importing students from Excel or CSV files.

    Expected columns:
    - first_name (required)
    - last_name (required)
    - date_of_birth (required: YYYY-MM-DD)
    - gender (required: Male or Female)
    - student_id (required)
    - admission_date (required: YYYY-MM-DD)
    - class_name (required: e.g., "Basic 1 A", "JHS 2 B" - must match existing class)
    - guardian_name (required)
    - guardian_phone (required)
    - other_names (optional)
    - email (optional)
    - phone_number (optional)
    - residential_address (optional)
    - guardian_relationship (optional: Parent, Father, Mother, Guardian, etc.)
    - guardian_email (optional)
    - guardian_address (optional)
    - emergency_contact_name (optional)
    - emergency_contact_phone (optional)
    - medical_conditions (optional)
    - create_account (optional: yes/no, true/false, 1/0)
    """
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered file-input-sm w-full',
            'accept': '.xlsx,.xls,.csv'
        }),
        help_text='Upload Excel (.xlsx, .xls) or CSV (.csv) file'
    )
    
    create_user_accounts = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        label='Create user accounts for students with email addresses',
        help_text='Enable to create login accounts for students who have email addresses'
    )

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise forms.ValidationError('Please upload a file.')
        
        file_name = file.name.lower()
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls') or file_name.endswith('.csv')):
            raise forms.ValidationError(
                'Invalid file format. Please upload an Excel (.xlsx, .xls) or CSV (.csv) file.'
            )
        
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 5MB.')
        
        return file

    def parse_file(self) -> List[Dict[str, Any]]:
        """Parse uploaded file and return list of student data."""
        file = self.cleaned_data['file']
        file_name = file.name.lower()
        
        if file_name.endswith('.csv'):
            return self._parse_csv(file)
        else:
            return self._parse_excel(file)

    def _parse_csv(self, file) -> List[Dict[str, Any]]:
        """Parse CSV file."""
        students = []
        file_wrapper = TextIOWrapper(file.file, encoding='utf-8-sig')
        csv_reader = csv.DictReader(file_wrapper)
        
        for row_num, row in enumerate(csv_reader, start=2):
            student_data = self._process_row(row, row_num)
            students.append(student_data)
        
        return students

    def _parse_excel(self, file) -> List[Dict[str, Any]]:
        """Parse Excel file."""
        students = []
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        
        # Get header row
        headers = []
        for cell in sheet[1]:
            headers.append(str(cell.value).strip().lower() if cell.value else '')
        
        # Process data rows
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = value
            
            if not any(row_dict.values()):
                continue
            
            student_data = self._process_row(row_dict, row_num)
            students.append(student_data)
        
        return students

    def _process_row(self, row: Dict[str, Any], row_num: int) -> Dict[str, Any]:
        """Process a single row and validate data."""
        data = {
            'row_num': row_num,
            'first_name': str(row.get('first_name', '')).strip(),
            'last_name': str(row.get('last_name', '')).strip(),
            'other_names': str(row.get('other_names', '')).strip(),
            'email': str(row.get('email', '')).strip().lower() if row.get('email') else '',
            'gender': str(row.get('gender', '')).strip().capitalize(),
            'phone_number': str(row.get('phone_number', '')).strip(),
            'residential_address': str(row.get('residential_address', '')).strip(),
            'student_id': str(row.get('student_id', '')).strip(),
            'admission_date': row.get('admission_date'),
            'date_of_birth': row.get('date_of_birth'),
            'class_name': str(row.get('class_name', '')).strip(),
            'guardian_name': str(row.get('guardian_name', '')).strip(),
            'guardian_relationship': str(row.get('guardian_relationship', 'Parent')).strip(),
            'guardian_phone': str(row.get('guardian_phone', '')).strip(),
            'guardian_email': str(row.get('guardian_email', '')).strip().lower() if row.get('guardian_email') else '',
            'guardian_address': str(row.get('guardian_address', '')).strip(),
            'emergency_contact_name': str(row.get('emergency_contact_name', '')).strip(),
            'emergency_contact_phone': str(row.get('emergency_contact_phone', '')).strip(),
            'medical_conditions': str(row.get('medical_conditions', '')).strip(),
            'create_account': row.get('create_account', ''),
            'errors': [],
            'valid': True
        }

        # Validate required fields
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender',
                          'student_id', 'admission_date', 'class_name',
                          'guardian_name', 'guardian_phone']
        for field in required_fields:
            if not data[field]:
                data['errors'].append(f'{field.replace("_", " ").title()} is required')
                data['valid'] = False
        
        # Validate gender
        if data['gender'] and data['gender'] not in ['Male', 'Female']:
            data['errors'].append(f'Gender must be Male or Female (got: {data["gender"]})')
            data['valid'] = False
        
        # Validate dates
        if data['admission_date']:
            data['admission_date'] = self._parse_date(data['admission_date'], 'Admission Date', data)
        
        if data['date_of_birth']:
            data['date_of_birth'] = self._parse_date(data['date_of_birth'], 'Date of Birth', data)
        
        # Validate student_id uniqueness
        if data['student_id']:
            if Student.objects.filter(student_id=data['student_id']).exists():
                data['errors'].append(f'Student ID {data["student_id"]} already exists')
                data['valid'] = False

        # Validate class_name (required - must exist and be active)
        if data['class_name']:
            from classes.models import Class
            if not Class.objects.filter(name=data['class_name'], is_active=True).exists():
                data['errors'].append(f'Class "{data["class_name"]}" not found or inactive')
                data['valid'] = False

        # Parse create_account field
        create_account_value = str(data['create_account']).strip().lower()
        data['create_account'] = create_account_value in ['yes', 'true', '1', 'y']

        return data

    def _parse_date(self, date_value: Any, field_name: str, data: Dict) -> Optional[str]:
        """Parse date value into YYYY-MM-DD format."""
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        elif isinstance(date_value, str):
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    parsed_date = datetime.strptime(date_value.strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            data['errors'].append(f'{field_name} has invalid format (use YYYY-MM-DD)')
            data['valid'] = False
            return None
        else:
            return None


class ProgrammeForm(forms.ModelForm):
    """Form for creating and editing programmes (for SHS schools)"""

    class Meta:
        model = Programme
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., General Science, Business, Visual Arts',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., SCI, BUS, VART',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Programme description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def clean_code(self):
        """Ensure programme code is uppercase"""
        code = self.cleaned_data.get('code')
        if code:
            return code.upper()
        return code
