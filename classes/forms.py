from django import forms
from .models import Subject, Class, ClassSubject, StudentEnrollment, House
from teachers.models import Teacher
from students.models import Student


class SubjectForm(forms.ModelForm):
    """Form for creating and editing subjects"""
    
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Mathematics, English Language',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., MATH101, ENG101',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Subject description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def clean_code(self):
        """Ensure subject code is uppercase"""
        code = self.cleaned_data.get('code')
        if code:
            return code.upper()
        return code


class ClassForm(forms.ModelForm):
    """Form for creating and editing classes following Ghana's Education System"""

    class Meta:
        model = Class
        fields = [
            'grade_level', 'section', 'programme', 'class_teacher',
            'capacity', 'academic_year', 'room_number', 'is_active'
        ]
        widgets = {
            'grade_level': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'section': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., A, B, C (optional)'
            }),
            'programme': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'class_teacher': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': 1,
                'max': 200,
                'required': True
            }),
            'academic_year': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Room 101, Block A (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }
        help_texts = {
            'grade_level': 'Select from Early Childhood (Nursery, KG), Basic Education (Basic 1-9), or SHS (SHS 1-3)',
            'section': 'Section identifier (e.g., A, B, C). Optional but recommended for multiple classes per grade',
            'programme': 'Academic programme - Required for SHS classes only (Science, Arts, Business, etc.)',
            'academic_year': 'Select the academic year for this class',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active teachers, programmes, and academic years
        self.fields['class_teacher'].queryset = Teacher.objects.filter(is_active=True)
        from students.models import Programme
        from core.models import AcademicYear
        self.fields['programme'].queryset = Programme.objects.filter(is_active=True)
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-start_date')
        # Make programme field help text more prominent
        self.fields['programme'].help_text = 'Only applicable to Senior High School (SHS 1-3) classes'

    def clean(self):
        """Validate form according to Ghana's education system rules"""
        cleaned_data = super().clean()
        grade_level = cleaned_data.get('grade_level')
        programme = cleaned_data.get('programme')

        if grade_level and programme:
            # Use Class model constants for validation
            # Non-SHS classes should not have a programme
            if grade_level not in Class.SHS_GRADES:
                raise forms.ValidationError({
                    'programme': f'Programmes are only applicable to Senior High School (SHS) classes. '
                                 f'{grade_level} is a {self._get_school_level_name(grade_level)} class.'
                })

        return cleaned_data

    def _get_school_level_name(self, grade_level):
        """Helper to get school level name for error messages"""
        if grade_level in Class.EARLY_CHILDHOOD_GRADES:
            return 'Early Childhood'
        elif grade_level in Class.PRIMARY_GRADES:
            return 'Primary School'
        elif grade_level in Class.JHS_GRADES:
            return 'Junior High School'
        return 'Unknown'

    def save(self, commit=True):
        """Save the form and validate the model"""
        instance = super().save(commit=False)
        if commit:
            # Call full_clean to run model validation
            instance.full_clean()
            instance.save()
        return instance


class ClassSubjectForm(forms.ModelForm):
    """Form for assigning subjects to classes"""

    class Meta:
        model = ClassSubject
        fields = ['subject', 'teacher', 'periods_per_week']
        widgets = {
            'subject': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'teacher': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'periods_per_week': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': 1,
                'max': 20,
                'value': 5
            }),
        }

    def __init__(self, *args, **kwargs):
        self.class_obj = kwargs.pop('class_obj', None)
        super().__init__(*args, **kwargs)
        # Only show active subjects and teachers
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True)

    def clean_subject(self):
        subject = self.cleaned_data.get('subject')
        if subject and self.class_obj:
            # Check if this subject is already assigned to this class (active or inactive)
            # This matches the database unique constraint
            existing = ClassSubject.objects.filter(
                class_obj=self.class_obj,
                subject=subject
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if existing.exists():
                if existing.first().is_active:
                    raise forms.ValidationError(
                        f'{subject.name} is already assigned to {self.class_obj.name}.'
                    )
                else:
                    raise forms.ValidationError(
                        f'{subject.name} was previously assigned to {self.class_obj.name}. '
                        f'Please reactivate it instead of creating a new assignment.'
                    )
        return subject


class StudentEnrollmentForm(forms.ModelForm):
    """Form for enrolling students in classes"""

    class Meta:
        model = StudentEnrollment
        fields = ['student', 'enrollment_date', 'roll_number', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'enrollment_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
                'required': True
            }),
            'roll_number': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': 1,
                'placeholder': 'Roll number (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Additional notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.class_obj = kwargs.pop('class_obj', None)
        super().__init__(*args, **kwargs)
        # Only show active students
        self.fields['student'].queryset = Student.objects.filter(is_active=True)

    def clean_student(self):
        student = self.cleaned_data.get('student')
        if student and self.class_obj:
            # Check if student is already enrolled for this academic year
            existing = StudentEnrollment.objects.filter(
                student=student,
                academic_year=self.class_obj.academic_year,
                is_active=True
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if existing.exists():
                raise forms.ValidationError(
                    f'{student.get_full_name()} is already enrolled in {existing.first().class_obj.name} '
                    f'for academic year {self.class_obj.academic_year}.'
                )
        return student


class BulkEnrollmentForm(forms.Form):
    """Form for enrolling multiple students in a class at once"""
    
    class_obj = forms.ModelChoiceField(
        queryset=Class.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm w-full',
            'required': True
        }),
        label='Class'
    )
    
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        label='Select Students'
    )
    
    enrollment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'input input-bordered input-sm w-full',
            'type': 'date',
            'required': True
        }),
        label='Enrollment Date'
    )


class HouseForm(forms.ModelForm):
    """Form for creating and editing houses"""

    class Meta:
        model = House
        fields = ['name', 'color', 'house_master', 'motto', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Red House, Blue House, Aggrey House',
                'required': True
            }),
            'color': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'color',
                'required': True
            }),
            'house_master': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full'
            }),
            'motto': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'House motto or slogan (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Additional information about the house (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active teachers
        self.fields['house_master'].queryset = Teacher.objects.filter(is_active=True)
        self.fields['house_master'].required = False
