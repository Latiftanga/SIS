"""
Grading and Assessment Models

This module implements a comprehensive grading system for Ghanaian schools:
- Flexible assessment types (tests, assignments, exams)
- Weighted scoring with continuous assessment
- Ghanaian grading scale (A1-F9)
- Term-based reporting
- Class rankings and analytics
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from classes.models import Class, ClassSubject, StudentEnrollment
from students.models import Student
from teachers.models import Teacher


class GradingPeriod(models.Model):
    """
    Represents grading configuration for a term/semester.
    Links to the Term model for term/semester information.
    """

    term = models.OneToOneField(
        'core.Term',
        on_delete=models.CASCADE,
        related_name='grading_period',
        help_text='Term/Semester this grading period is for'
    )
    start_date = models.DateField()
    end_date = models.DateField()

    # Grading deadlines
    grade_entry_deadline = models.DateField(
        help_text='Last date for teachers to enter grades'
    )
    report_generation_date = models.DateField(
        help_text='Date when report cards are generated'
    )

    is_current = models.BooleanField(
        default=False,
        help_text='Only one grading period can be current at a time'
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-term__academic_year__start_date', '-term__number']
        indexes = [
            models.Index(fields=['term']),
            models.Index(fields=['is_current']),
        ]

    def __str__(self):
        return f"{self.term}"

    def save(self, *args, **kwargs):
        # Ensure only one grading period is current
        if self.is_current:
            GradingPeriod.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('Start date must be before end date.')
        if self.grade_entry_deadline and self.end_date and self.grade_entry_deadline < self.end_date:
            raise ValidationError('Grade entry deadline should be after term end date.')


class AssessmentType(models.Model):
    """
    Defines types of assessments (Class Test, Assignment, Exam, etc.)
    with configurable weights for grade calculation.
    """

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text='Short code (e.g., CT, ASG, EXAM)'
    )
    description = models.TextField(blank=True)

    is_exam = models.BooleanField(
        default=False,
        help_text='Mark this if it is an end-of-term exam'
    )

    default_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Default weight percentage (0-100)'
    )

    default_max_score = models.PositiveIntegerField(
        default=100,
        help_text='Default maximum score for this assessment type'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_exam', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class SubjectAssessment(models.Model):
    """
    A specific assessment for a class-subject combination.
    Teachers create assessments and then enter grades for each student.
    """

    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    grading_period = models.ForeignKey(
        GradingPeriod,
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.PROTECT,
        related_name='assessments'
    )

    name = models.CharField(
        max_length=200,
        help_text='Specific name for this assessment (e.g., "Mid-Term Math Test")'
    )

    max_score = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text='Maximum possible score'
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Weight in final grade calculation (%)'
    )

    date_conducted = models.DateField()
    description = models.TextField(blank=True)

    is_published = models.BooleanField(
        default=False,
        help_text='Students can view their scores when published'
    )

    created_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assessments'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_conducted']
        indexes = [
            models.Index(fields=['class_subject', 'grading_period']),
            models.Index(fields=['grading_period', 'is_published']),
        ]

    def __str__(self):
        return f"{self.name} - {self.class_subject.subject.name}"

    def get_total_weight_for_period(self):
        """Calculate total weight of all assessments in this period for this subject"""
        return SubjectAssessment.objects.filter(
            class_subject=self.class_subject,
            grading_period=self.grading_period
        ).aggregate(
            total=models.Sum('weight')
        )['total'] or Decimal('0')

    def get_average_score(self):
        """Calculate average score for this assessment across all students"""
        grades = self.grades.filter(is_excused=False)
        if not grades.exists():
            return None
        return grades.aggregate(avg=models.Avg('score'))['avg']


class StudentGrade(models.Model):
    """
    Individual student's grade for a specific assessment.
    """

    assessment = models.ForeignKey(
        SubjectAssessment,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='grades',
        help_text='Links grade to specific enrollment'
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text='Score obtained (e.g., 85.5)'
    )

    is_excused = models.BooleanField(
        default=False,
        help_text='Student was absent/excused from this assessment'
    )

    remarks = models.TextField(
        blank=True,
        help_text='Teacher comments on this specific assessment'
    )

    graded_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_assessments'
    )
    graded_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['assessment', 'student']]
        ordering = ['student__last_name', 'student__first_name']
        indexes = [
            models.Index(fields=['assessment', 'student']),
            models.Index(fields=['student', 'enrollment']),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assessment.name}: {self.score}"

    def clean(self):
        if self.score is not None and self.score > self.assessment.max_score:
            raise ValidationError(
                f'Score cannot exceed maximum score of {self.assessment.max_score}'
            )

    def get_percentage(self):
        """Calculate score as percentage"""
        if self.score is None or self.is_excused:
            return None
        return (self.score / Decimal(str(self.assessment.max_score))) * 100

    def get_weighted_score(self):
        """Calculate weighted contribution to final grade"""
        percentage = self.get_percentage()
        if percentage is None:
            return None
        return (percentage * self.assessment.weight) / 100


class GradingScale(models.Model):
    """
    Ghanaian grading scale (A1-F9) with grade point mapping.
    This is typically standardized but can be customized per school.
    """

    grade = models.CharField(
        max_length=2,
        unique=True,
        help_text='Grade symbol (e.g., A1, B2, C3, etc.)'
    )
    min_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    interpretation = models.CharField(
        max_length=50,
        help_text='Grade interpretation (e.g., Excellent, Very Good)'
    )
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        help_text='Grade point for GPA calculation'
    )
    remarks = models.CharField(
        max_length=100,
        blank=True,
        help_text='Additional remarks for this grade range'
    )

    is_passing = models.BooleanField(
        default=True,
        help_text='Indicates if this grade is a passing grade'
    )

    class Meta:
        ordering = ['-min_score']

    def __str__(self):
        return f"{self.grade} ({self.min_score}-{self.max_score}%) - {self.interpretation}"

    @staticmethod
    def get_grade_for_score(score):
        """Get grade symbol for a given score"""
        if score is None:
            return None

        grade_scale = GradingScale.objects.filter(
            min_score__lte=score,
            max_score__gte=score
        ).first()

        return grade_scale.grade if grade_scale else None


class TermGrade(models.Model):
    """
    Aggregated grade for a student in a subject for an entire term.
    Automatically calculated from individual assessment scores.
    """

    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='term_grades'
    )
    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='term_grades'
    )
    grading_period = models.ForeignKey(
        GradingPeriod,
        on_delete=models.CASCADE,
        related_name='term_grades'
    )

    # Calculated scores
    continuous_assessment_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Sum of continuous assessment (non-exam) scores'
    )
    exam_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Exam score'
    )
    total_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Final weighted total score'
    )

    grade = models.CharField(
        max_length=2,
        blank=True,
        help_text='Letter grade (A1, B2, etc.)'
    )
    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )

    class_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Position in class for this subject'
    )

    teacher_comment = models.TextField(
        blank=True,
        help_text='Subject teacher comment'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['enrollment', 'class_subject', 'grading_period']]
        ordering = ['-total_score']
        indexes = [
            models.Index(fields=['grading_period', 'class_subject']),
            models.Index(fields=['enrollment', 'grading_period']),
        ]

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.class_subject.subject.name}: {self.grade}"

    def calculate_scores(self):
        """Calculate all scores from individual assessments"""
        assessments = SubjectAssessment.objects.filter(
            class_subject=self.class_subject,
            grading_period=self.grading_period
        )

        ca_total = Decimal('0')
        exam_total = Decimal('0')
        total = Decimal('0')

        for assessment in assessments:
            grade = StudentGrade.objects.filter(
                assessment=assessment,
                student=self.enrollment.student,
                is_excused=False
            ).first()

            if grade and grade.score is not None:
                weighted = grade.get_weighted_score()
                if weighted:
                    total += weighted
                    if assessment.assessment_type.is_exam:
                        exam_total += weighted
                    else:
                        ca_total += weighted

        self.continuous_assessment_score = ca_total
        self.exam_score = exam_total
        self.total_score = total

        # Get grade
        self.grade = GradingScale.get_grade_for_score(total) or ''

        # Get grade point
        if self.grade:
            grade_scale = GradingScale.objects.filter(grade=self.grade).first()
            if grade_scale:
                self.grade_point = grade_scale.grade_point

        self.save()


class ConductGrade(models.Model):
    """
    Student conduct/behavior grades for traits like punctuality, neatness, etc.
    """

    class ConductArea(models.TextChoices):
        ATTENDANCE = 'attendance', 'Attendance'
        PUNCTUALITY = 'punctuality', 'Punctuality'
        NEATNESS = 'neatness', 'Neatness'
        POLITENESS = 'politeness', 'Politeness'
        HONESTY = 'honesty', 'Honesty'
        LEADERSHIP = 'leadership', 'Leadership'
        RELATIONSHIP = 'relationship', 'Relationship with Others'
        ATTITUDE = 'attitude', 'Attitude to Work'

    class Rating(models.TextChoices):
        EXCELLENT = '5', 'Excellent'
        VERY_GOOD = '4', 'Very Good'
        GOOD = '3', 'Good'
        SATISFACTORY = '2', 'Satisfactory'
        NEEDS_IMPROVEMENT = '1', 'Needs Improvement'

    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='conduct_grades'
    )
    grading_period = models.ForeignKey(
        GradingPeriod,
        on_delete=models.CASCADE,
        related_name='conduct_grades'
    )

    conduct_area = models.CharField(
        max_length=20,
        choices=ConductArea.choices
    )
    rating = models.CharField(
        max_length=1,
        choices=Rating.choices
    )

    comments = models.TextField(blank=True)
    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['enrollment', 'grading_period', 'conduct_area']]
        ordering = ['conduct_area']

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.get_conduct_area_display()}: {self.get_rating_display()}"


class ReportCard(models.Model):
    """
    Complete report card for a student for a term.
    Aggregates all term grades, attendance, conduct, and comments.
    """

    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name='report_cards'
    )
    grading_period = models.ForeignKey(
        GradingPeriod,
        on_delete=models.CASCADE,
        related_name='report_cards'
    )

    # Overall metrics
    total_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Sum of all subject scores'
    )
    average_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Grade Point Average'
    )

    class_position = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Overall position in class'
    )
    total_students = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Total students in class'
    )

    # Attendance
    days_present = models.PositiveIntegerField(default=0)
    days_absent = models.PositiveIntegerField(default=0)
    days_school_opened = models.PositiveIntegerField(default=0)
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Comments
    class_teacher_comment = models.TextField(blank=True)
    head_teacher_comment = models.TextField(blank=True)

    # Promotion decision
    promoted_to = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promoted_from_reports',
        help_text='Class student is promoted to'
    )

    is_published = models.BooleanField(
        default=False,
        help_text='Report card visible to students/parents'
    )

    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['enrollment', 'grading_period']]
        ordering = ['-grading_period', '-average_score']
        indexes = [
            models.Index(fields=['grading_period', 'is_published']),
            models.Index(fields=['enrollment', 'grading_period']),
        ]

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.grading_period}"

    def calculate_overall_metrics(self):
        """Calculate overall GPA, position, etc."""
        term_grades = TermGrade.objects.filter(
            enrollment=self.enrollment,
            grading_period=self.grading_period
        )

        if term_grades.exists():
            # Calculate average and GPA
            total = sum(tg.total_score for tg in term_grades if tg.total_score)
            count = term_grades.count()

            self.total_score = total
            self.average_score = total / count if count > 0 else None

            gpa_sum = sum(tg.grade_point for tg in term_grades if tg.grade_point)
            self.gpa = gpa_sum / count if count > 0 else None

        # Calculate attendance
        from attendance.models import AttendanceRecord
        records = AttendanceRecord.objects.filter(
            student=self.enrollment.student,
            session__date__gte=self.grading_period.start_date,
            session__date__lte=self.grading_period.end_date
        )

        self.days_present = records.filter(status__in=['present', 'late']).count()
        self.days_absent = records.filter(status='absent').count()
        self.days_school_opened = records.values('session__date').distinct().count()

        if self.days_school_opened > 0:
            self.attendance_percentage = (self.days_present / self.days_school_opened) * 100

        self.save()
