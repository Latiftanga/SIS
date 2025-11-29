"""
Forms for the grading application.
"""
from django import forms
from .models import (
    GradingPeriod, AssessmentType, SubjectAssessment,
    StudentGrade, ConductGrade
)
from classes.models import ClassSubject
from teachers.models import Teacher


class GradingPeriodForm(forms.ModelForm):
    """Form for creating and editing grading periods"""

    class Meta:
        model = GradingPeriod
        fields = [
            'academic_year', 'term', 'start_date', 'end_date',
            'grade_entry_deadline', 'report_generation_date',
            'is_current', 'is_active'
        ]
        widgets = {
            'academic_year': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., 2024/2025',
                'required': True
            }),
            'term': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
                'required': True
            }),
            'grade_entry_deadline': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
                'required': True
            }),
            'report_generation_date': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def clean(self):
        """Validate date relationships"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        grade_entry_deadline = cleaned_data.get('grade_entry_deadline')

        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError('End date must be after start date.')

        if grade_entry_deadline and end_date:
            if grade_entry_deadline < end_date:
                self.add_error(
                    'grade_entry_deadline',
                    'Grade entry deadline should be on or after the term end date.'
                )

        return cleaned_data


class AssessmentTypeForm(forms.ModelForm):
    """Form for creating and editing assessment types"""

    class Meta:
        model = AssessmentType
        fields = [
            'name', 'code', 'description', 'is_exam',
            'default_weight', 'default_max_score', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Class Test, Mid-Term Exam',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., CT, MID, EXAM',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Description of this assessment type (optional)'
            }),
            'is_exam': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
            'default_weight': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'e.g., 5.00, 10.00, 70.00',
                'required': True
            }),
            'default_max_score': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': '1',
                'placeholder': 'e.g., 20, 100',
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def clean_code(self):
        """Ensure assessment type code is uppercase"""
        code = self.cleaned_data.get('code')
        if code:
            return code.upper()
        return code


class SubjectAssessmentForm(forms.ModelForm):
    """Form for creating and editing subject assessments"""

    class Meta:
        model = SubjectAssessment
        fields = [
            'name', 'class_subject', 'grading_period', 'assessment_type',
            'max_score', 'weight', 'date_conducted', 'description', 'is_published'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'placeholder': 'e.g., Class Test 1, First Term Exam',
                'required': True
            }),
            'class_subject': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'grading_period': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'assessment_type': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': '1',
                'placeholder': 'e.g., 20, 100',
                'required': True
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'e.g., 5.00, 10.00',
                'required': True
            }),
            'date_conducted': forms.DateInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'type': 'date',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Assessment details (optional)'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            }),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form and populate initial values from assessment type"""
        super().__init__(*args, **kwargs)

        # If creating a new assessment and assessment_type is selected
        if not self.instance.pk and 'assessment_type' in self.data:
            try:
                assessment_type_id = int(self.data.get('assessment_type'))
                assessment_type = AssessmentType.objects.get(pk=assessment_type_id)
                # Pre-fill weight and max_score from assessment type defaults
                if not self.data.get('weight'):
                    self.fields['weight'].initial = assessment_type.default_weight
                if not self.data.get('max_score'):
                    self.fields['max_score'].initial = assessment_type.default_max_score
            except (ValueError, TypeError, AssessmentType.DoesNotExist):
                pass


class StudentGradeForm(forms.ModelForm):
    """Form for creating and editing student grades"""

    class Meta:
        model = StudentGrade
        fields = ['score', 'is_excused', 'remarks']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'input input-bordered input-sm w-full',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'is_excused': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-sm'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered textarea-sm w-full',
                'rows': 2,
                'placeholder': 'Optional remarks'
            }),
        }

    def __init__(self, *args, assessment=None, **kwargs):
        """Initialize with assessment to set max score validation"""
        super().__init__(*args, **kwargs)
        self.assessment = assessment

        if assessment:
            self.fields['score'].widget.attrs['max'] = str(assessment.max_score)
            self.fields['score'].widget.attrs['placeholder'] = f'Max: {assessment.max_score}'

    def clean_score(self):
        """Validate score is within assessment max score"""
        score = self.cleaned_data.get('score')
        is_excused = self.cleaned_data.get('is_excused')

        if is_excused:
            # If excused, score can be null
            return None

        if score is not None and self.assessment:
            if score > self.assessment.max_score:
                raise forms.ValidationError(
                    f'Score cannot exceed maximum score of {self.assessment.max_score}'
                )
            if score < 0:
                raise forms.ValidationError('Score cannot be negative')

        return score


class ConductGradeForm(forms.ModelForm):
    """Form for creating and editing conduct grades"""

    class Meta:
        model = ConductGrade
        fields = ['conduct_area', 'rating', 'comments']
        widgets = {
            'conduct_area': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'rating': forms.Select(attrs={
                'class': 'select select-bordered select-sm w-full',
                'required': True
            }),
            'comments': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered textarea-sm w-full',
                'rows': 2,
                'placeholder': 'Optional comments on conduct'
            }),
        }
