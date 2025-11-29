from django import forms
from .models import AttendanceSession, AttendanceRecord


class AttendanceSessionForm(forms.ModelForm):
    """Form for creating a new attendance session"""

    class Meta:
        model = AttendanceSession
        fields = ['date', 'session_type', 'subject', 'period_number', 'notes']

    def __init__(self, *args, **kwargs):
        self.class_obj = kwargs.pop('class_obj', None)
        super().__init__(*args, **kwargs)

        # Configure subject field to only show subjects for this class
        if self.class_obj:
            from classes.models import ClassSubject
            self.fields['subject'].queryset = ClassSubject.objects.filter(
                class_obj=self.class_obj,
                is_active=True
            )

        # Make subject and period_number optional for daily attendance
        self.fields['subject'].required = False
        self.fields['period_number'].required = False

    def clean(self):
        cleaned_data = super().clean()
        session_type = cleaned_data.get('session_type')
        subject = cleaned_data.get('subject')

        # If subject-specific attendance, subject is required
        if session_type == AttendanceSession.SessionType.SUBJECT and not subject:
            raise forms.ValidationError('Subject is required for subject-specific attendance.')

        return cleaned_data


class BulkAttendanceForm(forms.Form):
    """Form for marking attendance for multiple students at once"""

    def __init__(self, *args, **kwargs):
        students = kwargs.pop('students', [])
        existing_records = kwargs.pop('existing_records', {})
        super().__init__(*args, **kwargs)

        # Create fields for each student
        for student in students:
            # Status field
            status_field_name = f'status_{student.id}'
            existing_record = existing_records.get(student.id)
            initial_status = existing_record.status if existing_record else AttendanceRecord.Status.PRESENT

            self.fields[status_field_name] = forms.ChoiceField(
                choices=AttendanceRecord.Status.choices,
                initial=initial_status,
                widget=forms.Select(attrs={'class': 'select select-bordered select-xs'})
            )

            # Time in field (for late arrivals)
            time_field_name = f'time_in_{student.id}'
            initial_time = existing_record.time_in if existing_record else None

            self.fields[time_field_name] = forms.TimeField(
                required=False,
                initial=initial_time,
                widget=forms.TimeInput(attrs={
                    'type': 'time',
                    'class': 'input input-bordered input-xs'
                })
            )

            # Remarks field
            remarks_field_name = f'remarks_{student.id}'
            initial_remarks = existing_record.remarks if existing_record else ''

            self.fields[remarks_field_name] = forms.CharField(
                required=False,
                initial=initial_remarks,
                widget=forms.TextInput(attrs={
                    'class': 'input input-bordered input-xs',
                    'placeholder': 'Optional notes...'
                })
            )
