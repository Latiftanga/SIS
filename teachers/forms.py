from typing import Optional, Tuple, List, Dict, Any
from django import forms
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from .models import Teacher
from accounts.utils import generate_secure_password
from core.models import SchoolSettings
import openpyxl
import csv
from io import TextIOWrapper
from datetime import datetime

User = get_user_model()


class TeacherCreateForm(forms.ModelForm):
    """
    Form for creating a new teacher with optional user account.

    Best Practices Implemented:
    - Optional user account creation via checkbox
    - Auto-generated secure passwords
    - Email notifications with credentials
    - Force password change on first login
    - Compact UI with smaller input fields
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
        help_text='Enable this to create a login account for the teacher'
    )

    class Meta:
        model = Teacher
        fields = [
            'first_name', 'last_name', 'other_names',
            'email', 'gender', 'date_of_birth', 'phone_number',
            'employee_id', 'date_joined'
        ]
        widgets = {
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
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'email@example.com',
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': '+233XXXXXXXXX or 0XXXXXXXXX',
                'required': True
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'Employee ID',
                'required': True
            }),
            'date_joined': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
                'required': True
            }),
        }

    def clean_email(self) -> str:
        """Validate email uniqueness if creating user account."""
        email = self.cleaned_data.get('email')
        create_user_account = self.data.get('create_user_account')

        # Check if email already exists in Teacher model
        if email:
            # Exclude current instance if editing
            qs = Teacher.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A teacher with this email already exists.')

            # Check User model only if creating user account
            if create_user_account and User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    'A user account with this email already exists. '
                    'Uncheck "Create user account" if you only want to create a teacher profile.'
                )

        return email

    def clean_employee_id(self) -> str:
        """Validate that employee_id is unique."""
        employee_id = self.cleaned_data.get('employee_id')
        if employee_id:
            qs = Teacher.objects.filter(employee_id=employee_id)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A teacher with this employee ID already exists.')
        return employee_id

    def _create_user_account(self, email: str) -> Tuple[User, str]:
        """
        Create user account with auto-generated password.

        Returns:
            Tuple[User, str]: Created user and generated password
        """
        # Generate secure password (8 characters - user-friendly)
        password = generate_secure_password()

        # Create user account
        user = User.objects.create_teacher(email=email, password=password)

        # Set force password change
        user.force_password_change = True
        user.save()

        return user, password

    def _send_welcome_email(
        self,
        teacher: Teacher,
        password: Optional[str] = None,
        request = None
    ) -> None:
        """
        Send welcome email to teacher.

        Args:
            teacher: The teacher instance
            password: Generated password (if user account created)
            request: HTTP request object for building URLs
        """
        # Get school settings
        school_settings = SchoolSettings.get_settings()
        school_name = school_settings.short_name if school_settings else 'SmartSIS'

        # Build login URL
        if request:
            domain = get_current_site(request).domain
            protocol = 'https' if request.is_secure() else 'http'
            login_url = f"{protocol}://{domain}/accounts/login/"
        else:
            login_url = "http://localhost:8000/accounts/login/"

        # Prepare email context
        context = {
            'teacher_name': teacher.get_full_name(),
            'school_name': school_name,
            'user_account_created': teacher.user is not None,
            'email': teacher.email,
            'password': password,
            'login_url': login_url,
        }

        # Render email templates
        html_message = render_to_string('emails/teacher_welcome.html', context)
        plain_message = render_to_string('emails/teacher_welcome.txt', context)

        # Send email
        send_mail(
            subject=f'Welcome to {school_name}!',
            message=plain_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL
            recipient_list=[teacher.email],
            html_message=html_message,
            fail_silently=False,
        )

    def save(self, commit: bool = True, request = None) -> Tuple[Teacher, Optional[str]]:
        """
        Create teacher profile and optionally user account.

        Args:
            commit: Whether to save to database
            request: HTTP request object for email URL building

        Returns:
            Tuple[Teacher, Optional[str]]: Created teacher and password (if generated)
        """
        teacher = super().save(commit=False)
        user = None
        password = None

        # Create user account if checkbox is checked
        if self.cleaned_data.get('create_user_account'):
            user, password = self._create_user_account(teacher.email)
            teacher.user = user

        if commit:
            teacher.save()

            # Send welcome email
            self._send_welcome_email(teacher, password, request)

        return teacher, password


class TeacherBulkImportForm(forms.Form):
    """
    Form for bulk importing teachers from Excel or CSV files.

    Supported file formats:
    - Excel (.xlsx, .xls)
    - CSV (.csv)

    Expected columns:
    - first_name (required)
    - last_name (required)
    - email (required)
    - gender (required: Male or Female)
    - phone_number (required)
    - employee_id (required)
    - date_joined (required: YYYY-MM-DD)
    - other_names (optional)
    - date_of_birth (optional: YYYY-MM-DD)
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
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        label='Create user accounts for all teachers',
        help_text='Enable to create login accounts for all imported teachers'
    )

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError('Please upload a file.')

        # Check file extension
        file_name = file.name.lower()
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls') or file_name.endswith('.csv')):
            raise forms.ValidationError(
                'Invalid file format. Please upload an Excel (.xlsx, .xls) or CSV (.csv) file.'
            )

        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError('File size must be less than 5MB.')

        return file

    def parse_file(self) -> List[Dict[str, Any]]:
        """
        Parse uploaded file and return list of teacher data.

        Returns:
            List of dictionaries containing teacher data with validation errors
        """
        file = self.cleaned_data['file']
        file_name = file.name.lower()

        if file_name.endswith('.csv'):
            return self._parse_csv(file)
        else:
            return self._parse_excel(file)

    def _parse_csv(self, file) -> List[Dict[str, Any]]:
        """Parse CSV file."""
        teachers = []
        file_wrapper = TextIOWrapper(file.file, encoding='utf-8-sig')
        csv_reader = csv.DictReader(file_wrapper)

        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (1 is header)
            teacher_data = self._process_row(row, row_num)
            teachers.append(teacher_data)

        return teachers

    def _parse_excel(self, file) -> List[Dict[str, Any]]:
        """Parse Excel file."""
        teachers = []
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active

        # Get header row
        headers = []
        for cell in sheet[1]:
            headers.append(str(cell.value).strip().lower() if cell.value else '')

        # Process data rows
        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            # Create dictionary from row data
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = value

            # Skip empty rows
            if not any(row_dict.values()):
                continue

            teacher_data = self._process_row(row_dict, row_num)
            teachers.append(teacher_data)

        return teachers

    def _process_row(self, row: Dict[str, Any], row_num: int) -> Dict[str, Any]:
        """
        Process a single row and validate data.

        Args:
            row: Dictionary containing row data
            row_num: Row number for error reporting

        Returns:
            Dictionary with processed data and validation errors
        """
        data = {
            'row_num': row_num,
            'first_name': str(row.get('first_name', '')).strip(),
            'last_name': str(row.get('last_name', '')).strip(),
            'other_names': str(row.get('other_names', '')).strip(),
            'email': str(row.get('email', '')).strip().lower(),
            'gender': str(row.get('gender', '')).strip().capitalize(),
            'phone_number': str(row.get('phone_number', '')).strip(),
            'employee_id': str(row.get('employee_id', '')).strip(),
            'date_joined': row.get('date_joined'),
            'date_of_birth': row.get('date_of_birth'),
            'create_account': row.get('create_account', ''),
            'errors': [],
            'valid': True
        }

        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'gender', 'phone_number', 'employee_id', 'date_joined']
        for field in required_fields:
            if not data[field]:
                data['errors'].append(f'{field.replace("_", " ").title()} is required')
                data['valid'] = False

        # Validate gender
        if data['gender'] and data['gender'] not in ['Male', 'Female']:
            data['errors'].append(f'Gender must be Male or Female (got: {data["gender"]})')
            data['valid'] = False

        # Validate dates
        if data['date_joined']:
            data['date_joined'] = self._parse_date(data['date_joined'], 'Date Joined', data)

        if data['date_of_birth']:
            data['date_of_birth'] = self._parse_date(data['date_of_birth'], 'Date of Birth', data)

        # Validate email uniqueness
        if data['email']:
            if Teacher.objects.filter(email=data['email']).exists():
                data['errors'].append(f'Email {data["email"]} already exists')
                data['valid'] = False

        # Validate employee_id uniqueness
        if data['employee_id']:
            if Teacher.objects.filter(employee_id=data['employee_id']).exists():
                data['errors'].append(f'Employee ID {data["employee_id"]} already exists')
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
            # Try common date formats
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
