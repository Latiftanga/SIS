from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from teachers.models import Teacher
from students.models import Student


class Subject(models.Model):
    """
    Represents a subject taught in the school (e.g., Mathematics, English, Science).

    Ghana's Education System Subject Classification:
    - Core Subjects: Mandatory for all students (e.g., English, Mathematics, Integrated Science, Social Studies)
    - Elective Subjects: Based on programme (e.g., Physics, Chemistry, Biology for Science students)
    - Co-Curricular: Extra-curricular activities (e.g., Physical Education, ICT)
    """

    class SubjectType(models.TextChoices):
        CORE = 'core', 'Core Subject'
        ELECTIVE = 'elective', 'Elective Subject'
        CO_CURRICULAR = 'co_curricular', 'Co-Curricular'

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Subject name (e.g., Mathematics, English)'
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Subject code (e.g., MATH101, ENG101)'
    )
    description = models.TextField(
        blank=True,
        help_text='Subject description'
    )

    # Ghana-specific fields
    subject_type = models.CharField(
        max_length=20,
        choices=SubjectType.choices,
        default=SubjectType.ELECTIVE,
        help_text='Core subjects are mandatory for all students'
    )
    credit_hours = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Subject credit hours/weight per week'
    )
    applicable_levels = models.JSONField(
        default=list,
        blank=True,
        help_text='Grade levels this subject applies to (e.g., ["SHS 1", "SHS 2", "SHS 3"])'
    )

    is_active = models.BooleanField(
        default=True,
        help_text='Whether this subject is currently offered'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['subject_type', 'name']
        verbose_name = 'subject'
        verbose_name_plural = 'subjects'
        indexes = [
            models.Index(fields=['subject_type', 'is_active']),
            models.Index(fields=['code']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def is_core_subject(self) -> bool:
        """Check if this is a core subject"""
        return self.subject_type == self.SubjectType.CORE

    def is_elective_subject(self) -> bool:
        """Check if this is an elective subject"""
        return self.subject_type == self.SubjectType.ELECTIVE


class Class(models.Model):
    """
    Represents a class/grade in the school following Ghana's Education System.

    Ghana's education structure (2007 Education Reform):
    - Early Childhood: Nursery, KG 1-2 (2 years)
    - Basic Education (11 years total):
      * Basic 1-6: Primary School (6 years, ages 6-11)
      * Basic 7-9: Junior High School/JHS (3 years, ages 12-14)
        - Basic 9 culminates in BECE (Basic Education Certificate Examination)
    - Senior High School (SHS): SHS 1-3 (3 years, ages 15-17)
      - SHS 3 culminates in WASSCE (West African Senior School Certificate Examination)

    Name is auto-generated from grade_level + section.
    For SHS classes, programme can be included in name (e.g., "SHS 2 Science A").
    """

    # Grade level group constants for reusability
    EARLY_CHILDHOOD_GRADES = ['Nursery', 'KG 1', 'KG 2']
    PRIMARY_GRADES = ['Basic 1', 'Basic 2', 'Basic 3', 'Basic 4', 'Basic 5', 'Basic 6']
    JHS_GRADES = ['Basic 7', 'Basic 8', 'Basic 9']
    SHS_GRADES = ['SHS 1', 'SHS 2', 'SHS 3']

    class GradeLevel(models.TextChoices):
        # Early Childhood Education (Ages 4-5)
        NURSERY = 'Nursery', 'Nursery'
        KG1 = 'KG 1', 'KG 1'
        KG2 = 'KG 2', 'KG 2'

        # Basic Education (Basic 1-9)
        # Primary Level (Basic 1-6, Ages 6-11)
        BASIC_1 = 'Basic 1', 'Basic 1'
        BASIC_2 = 'Basic 2', 'Basic 2'
        BASIC_3 = 'Basic 3', 'Basic 3'
        BASIC_4 = 'Basic 4', 'Basic 4'
        BASIC_5 = 'Basic 5', 'Basic 5'
        BASIC_6 = 'Basic 6', 'Basic 6'

        # Junior High School Level (Basic 7-9, Ages 12-14)
        BASIC_7 = 'Basic 7', 'Basic 7 (JHS 1)'
        BASIC_8 = 'Basic 8', 'Basic 8 (JHS 2)'
        BASIC_9 = 'Basic 9', 'Basic 9 (JHS 3 - BECE Year)'

        # Senior High School (SHS 1-3, Ages 15-17)
        SHS_1 = 'SHS 1', 'SHS 1'
        SHS_2 = 'SHS 2', 'SHS 2'
        SHS_3 = 'SHS 3', 'SHS 3 (WASSCE Year)'

    name = models.CharField(
        max_length=100,
        editable=False,
        help_text='Auto-generated from grade level and section'
    )
    grade_level = models.CharField(
        max_length=50,
        choices=GradeLevel.choices,
        help_text='Select grade/level'
    )
    section = models.CharField(
        max_length=10,
        blank=True,
        help_text='Section/stream (e.g., A, B, C, Science, Arts)'
    )
    
    # Class teacher (homeroom teacher)
    class_teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homeroom_classes',
        help_text='Class teacher/Form master'
    )

    # Programme (for SHS classes only - optional)
    programme = models.ForeignKey(
        'students.Programme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes',
        help_text='Academic programme (for SHS classes only - e.g., Science, Business, Visual Arts)'
    )

    # Capacity
    capacity = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        help_text='Maximum number of students'
    )
    
    # Academic year
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.PROTECT,
        related_name='classes',
        null=True,
        blank=True,
        help_text='Academic year for this class'
    )
    
    # Room information
    room_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Classroom number/location'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this class is currently active'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['grade_level', 'section', 'name']
        verbose_name = 'class'
        verbose_name_plural = 'classes'
        unique_together = [['grade_level', 'section', 'academic_year']]
        indexes = [
            models.Index(fields=['grade_level', 'is_active']),
            models.Index(fields=['academic_year', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        """Auto-generate class name from grade_level and section"""
        if self.section:
            self.name = f"{self.grade_level} {self.section}"
        else:
            self.name = self.grade_level
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
    
    def get_student_count(self) -> int:
        """Get the number of enrolled students"""
        return self.enrollments.filter(is_active=True).count()
    
    def get_available_capacity(self) -> int:
        """Get remaining capacity"""
        return self.capacity - self.get_student_count()
    
    def is_full(self) -> bool:
        """Check if class is at capacity"""
        return self.get_student_count() >= self.capacity

    def has_capacity(self) -> bool:
        """Check if class has available capacity for more students"""
        return not self.is_full()

    # Ghana Education System Helper Methods

    def is_early_childhood(self) -> bool:
        """Check if this is an early childhood class (Nursery, KG)"""
        return self.grade_level in self.EARLY_CHILDHOOD_GRADES

    def is_primary(self) -> bool:
        """Check if this is a primary class (Basic 1-6)"""
        return self.grade_level in self.PRIMARY_GRADES

    def is_jhs(self) -> bool:
        """Check if this is a JHS class (Basic 7-9)"""
        return self.grade_level in self.JHS_GRADES

    def is_basic_education(self) -> bool:
        """Check if this is part of basic education (Basic 1-9)"""
        return self.is_primary() or self.is_jhs()

    def is_shs(self) -> bool:
        """Check if this is an SHS class (SHS 1-3)"""
        return self.grade_level in self.SHS_GRADES

    def get_school_level(self) -> str:
        """Get the school level category"""
        if self.is_early_childhood():
            return 'Early Childhood'
        elif self.is_primary():
            return 'Primary School'
        elif self.is_jhs():
            return 'Junior High School'
        elif self.is_shs():
            return 'Senior High School'
        return 'Unknown'

    def requires_programme(self) -> bool:
        """Check if this class requires a programme (SHS only)"""
        return self.is_shs()

    def clean(self):
        """Validate model fields according to Ghana's education system"""
        from django.core.exceptions import ValidationError

        # Non-SHS classes should not have a programme
        # Note: This validation is also in ClassForm.clean() for better user feedback
        if not self.is_shs() and self.programme:
            raise ValidationError({
                'programme': 'Programmes are only applicable to Senior High School (SHS) classes.'
            })

        super().clean()


class ClassSubject(models.Model):
    """
    Links subjects to classes with assigned teachers.
    Represents which subjects are taught in which classes and by whom.
    """
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_subjects',
        verbose_name='Class'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_assignments'
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_assignments',
        help_text='Teacher assigned to teach this subject in this class'
    )
    
    # Schedule information (optional - can be expanded to full timetable later)
    periods_per_week = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text='Number of periods per week'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this subject is currently being taught'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['class_obj', 'subject']
        ordering = ['class_obj', 'subject']
        verbose_name = 'class subject'
        verbose_name_plural = 'class subjects'
        indexes = [
            models.Index(fields=['class_obj', 'is_active']),
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['subject', 'is_active']),
        ]

    def __str__(self) -> str:
        teacher_name = self.teacher.get_full_name() if self.teacher else 'No teacher'
        return f"{self.class_obj.name} - {self.subject.name} ({teacher_name})"


class StudentEnrollment(models.Model):
    """
    Tracks student enrollment in classes.
    Maintains complete historical record of student's academic journey.
    Each enrollment represents one academic year in one class.
    """

    class EnrollmentStatus(models.TextChoices):
        ENROLLED = 'enrolled', 'Currently Enrolled'
        COMPLETED = 'completed', 'Completed'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        TRANSFERRED = 'transferred', 'Transferred Out'

    class FinalResult(models.TextChoices):
        PROMOTED = 'promoted', 'Promoted to Next Grade'
        REPEATED = 'repeated', 'Repeated Grade'
        GRADUATED = 'graduated', 'Graduated'
        TRANSFERRED = 'transferred', 'Transferred'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        PENDING = 'pending', 'Pending (Year Not Complete)'

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Class'
    )

    # Academic year tracking
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.PROTECT,
        related_name='enrollments',
        null=True,
        blank=True,
        help_text='Academic year for this enrollment',
        db_index=True
    )

    # Enrollment dates
    enrollment_date = models.DateField(
        help_text='Date student was enrolled in this class'
    )
    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date student completed/left this class'
    )

    # Roll number (position in class)
    roll_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Student roll number in this class'
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ENROLLED,
        help_text='Current status of this enrollment'
    )

    final_result = models.CharField(
        max_length=20,
        choices=FinalResult.choices,
        default=FinalResult.PENDING,
        blank=True,
        help_text='Final outcome of this enrollment'
    )

    # Active flag (True only for current academic year)
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this is the current enrollment (current academic year only)',
        db_index=True
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this enrollment'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-academic_year', '-enrollment_date', 'roll_number']
        verbose_name = 'student enrollment'
        verbose_name_plural = 'student enrollments'
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['class_obj', 'is_active']),
            models.Index(fields=['academic_year', 'is_active']),
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['status', 'academic_year']),
            models.Index(fields=['final_result']),
            models.Index(fields=['status']),
        ]
        unique_together = [['student', 'academic_year']]  # One enrollment per student per year

    def __str__(self) -> str:
        return f"{self.student.get_full_name()} in {self.class_obj.name} ({self.academic_year})"

    def complete_enrollment(self, completion_date, final_result):
        """Mark enrollment as completed with final result"""
        self.completion_date = completion_date
        self.final_result = final_result
        self.status = self.EnrollmentStatus.COMPLETED
        self.is_active = False
        self.save()

    def is_current_year(self) -> bool:
        """Check if this is the current academic year enrollment"""
        return self.is_active and self.status == self.EnrollmentStatus.ENROLLED


class House(models.Model):
    """
    Represents school houses for inter-house competitions.

    Ghana schools traditionally use house systems (typically color-coded) for:
    - Sports competitions (Athletics, Football, etc.)
    - Academic competitions
    - Discipline and student organization
    - Building school spirit and healthy competition

    Common house colors: Red, Blue, Green, Yellow, Purple, Orange
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text='House name (e.g., Red House, Blue House, Aggrey House)'
    )
    color = models.CharField(
        max_length=7,
        help_text='Hex color code (e.g., #FF0000 for red, #0000FF for blue)'
    )
    house_master = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='houses',
        help_text='Teacher in charge of this house'
    )
    motto = models.CharField(
        max_length=200,
        blank=True,
        help_text='House motto or slogan'
    )
    description = models.TextField(
        blank=True,
        help_text='Additional information about the house'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this house is currently active'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'house'
        verbose_name_plural = 'houses'

    def __str__(self) -> str:
        return self.name


class NationalExamRegistration(models.Model):
    """
    Tracks student registrations for national examinations.

    Ghana's National Examinations:
    - BECE (Basic Education Certificate Examination): Taken at the end of Basic 9 (JHS 3)
    - WASSCE (West African Senior School Certificate Examination): Taken at the end of SHS 3

    Each student receives a unique index number for the exam.
    """

    class ExamType(models.TextChoices):
        BECE = 'bece', 'Basic Education Certificate Examination (BECE)'
        WASSCE = 'wassce', 'West African Senior School Certificate Examination (WASSCE)'

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='exam_registrations',
        help_text='Student registered for the exam'
    )
    exam_type = models.CharField(
        max_length=10,
        choices=ExamType.choices,
        help_text='Type of national examination'
    )
    exam_year = models.PositiveIntegerField(
        help_text='Year of examination (e.g., 2024)'
    )
    index_number = models.CharField(
        max_length=20,
        unique=True,
        help_text='National exam index number assigned to the student'
    )
    exam_center = models.CharField(
        max_length=200,
        help_text='Name of the examination center'
    )
    exam_center_code = models.CharField(
        max_length=20,
        blank=True,
        help_text='Official exam center code'
    )
    registration_date = models.DateField(
        help_text='Date student was registered for the exam'
    )
    is_school_candidate = models.BooleanField(
        default=True,
        help_text='False for private candidates'
    )

    # Results (to be filled after exam)
    results_received = models.BooleanField(
        default=False,
        help_text='Whether results have been received'
    )
    aggregate_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Aggregate score (for BECE) or total grade (for WASSCE)'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the registration'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['student', 'exam_type', 'exam_year']]
        ordering = ['-exam_year', 'exam_type', 'student']
        verbose_name = 'national exam registration'
        verbose_name_plural = 'national exam registrations'
        indexes = [
            models.Index(fields=['exam_type', 'exam_year']),
            models.Index(fields=['student', 'exam_type']),
            models.Index(fields=['index_number']),
        ]

    def __str__(self) -> str:
        return f"{self.student.get_full_name()} - {self.get_exam_type_display()} {self.exam_year}"

    def is_bece(self) -> bool:
        """Check if this is a BECE registration"""
        return self.exam_type == self.ExamType.BECE

    def is_wassce(self) -> bool:
        """Check if this is a WASSCE registration"""
        return self.exam_type == self.ExamType.WASSCE


class AssessmentStructure(models.Model):
    """
    Defines the assessment structure (CA vs Exam weightage) for different school levels.

    Ghana's Assessment Structure:
    - Basic Education (Basic 1-9): 30% Continuous Assessment + 70% End-of-Term Exam
    - Senior High School (SHS 1-3): 50% Continuous Assessment + 50% End-of-Term Exam

    This model allows schools to configure these weights if needed.
    """

    class SchoolLevel(models.TextChoices):
        EARLY_CHILDHOOD = 'early_childhood', 'Early Childhood (Nursery, KG)'
        BASIC = 'basic', 'Basic Education (Basic 1-9)'
        SHS = 'shs', 'Senior High School (SHS 1-3)'

    school_level = models.CharField(
        max_length=20,
        choices=SchoolLevel.choices,
        unique=True,
        help_text='School level this assessment structure applies to'
    )
    continuous_assessment_weight = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage weight for continuous assessment (0-100)'
    )
    exam_weight = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage weight for end-of-term examination (0-100)'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the assessment structure'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this assessment structure is currently in use'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['school_level']
        verbose_name = 'assessment structure'
        verbose_name_plural = 'assessment structures'

    def __str__(self) -> str:
        return f"{self.get_school_level_display()}: {self.continuous_assessment_weight}% CA + {self.exam_weight}% Exam"

    def clean(self):
        """Validate that weights sum to 100%"""
        from django.core.exceptions import ValidationError
        if self.continuous_assessment_weight + self.exam_weight != 100:
            raise ValidationError(
                'Continuous Assessment and Exam weights must sum to 100%'
            )
        super().clean()


class ClassPrefect(models.Model):
    """
    Tracks class prefects and their leadership positions.

    Ghana schools have class prefect systems where students are appointed
    to leadership roles within their classes for discipline, academics,
    sanitation, and other responsibilities.

    Prefects are typically appointed per term and can be reappointed.
    """

    class Position(models.TextChoices):
        PREFECT = 'prefect', 'Class Prefect'
        ASSISTANT = 'assistant', 'Assistant Class Prefect'
        ACADEMIC = 'academic', 'Academic Prefect'
        SANITATION = 'sanitation', 'Sanitation Prefect'
        ENTERTAINMENT = 'entertainment', 'Entertainment Prefect'
        SPORTS = 'sports', 'Sports Prefect'

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='prefects',
        verbose_name='Class',
        help_text='Class this prefect belongs to'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='prefect_positions',
        help_text='Student appointed as prefect'
    )
    position = models.CharField(
        max_length=20,
        choices=Position.choices,
        help_text='Leadership position'
    )
    appointed_date = models.DateField(
        help_text='Date student was appointed'
    )
    term = models.ForeignKey(
        'core.Term',
        on_delete=models.CASCADE,
        related_name='class_prefects',
        help_text='Academic term for this appointment'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this prefect position is currently active'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the appointment'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['class_obj', 'position', 'term', 'is_active']]
        ordering = ['-term', 'class_obj', 'position']
        verbose_name = 'class prefect'
        verbose_name_plural = 'class prefects'
        indexes = [
            models.Index(fields=['class_obj', 'is_active']),
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['term', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.student.get_full_name()} - {self.get_position_display()} ({self.class_obj.name})"
