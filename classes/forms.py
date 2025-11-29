from django import forms
from .models import Subject, Class, ClassSubject, StudentEnrollment
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
    """Form for creating and editing classes"""

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
            'academic_year': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., 2024/2025',
                'required': True
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Room 101, Block A (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active teachers and programmes
        self.fields['class_teacher'].queryset = Teacher.objects.filter(is_active=True)
        from students.models import Programme
        self.fields['programme'].queryset = Programme.objects.filter(is_active=True)


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
