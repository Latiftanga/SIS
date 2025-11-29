"""
Management command to set up the default Ghanaian grading scale.
Run this command once per tenant to initialize the grading scale.

Usage: python manage.py setup_grading_scale
"""

from django.core.management.base import BaseCommand
from django.db import connection
from grading.models import GradingScale, AssessmentType
from schools.models import School


class Command(BaseCommand):
    help = 'Set up default Ghanaian grading scale (A1-F9) and assessment types'

    def handle(self, *args, **options):
        # Get all tenants
        tenants = School.objects.exclude(schema_name='public')

        if not tenants.exists():
            self.stdout.write(self.style.WARNING('No tenants found. Please create a school first.'))
            return

        # Run setup for each tenant
        for tenant in tenants:
            connection.set_tenant(tenant)
            self.setup_for_tenant(tenant)

    def setup_for_tenant(self, tenant):
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'Setting up for tenant: {tenant.schema_name} ({tenant.name})')
        self.stdout.write(f'{"="*60}')

        # Define the Ghanaian grading scale
        grading_data = [
            {
                'grade': 'A1',
                'min_score': 80.00,
                'max_score': 100.00,
                'interpretation': 'Excellent',
                'grade_point': 4.00,
                'is_passing': True,
                'remarks': 'Outstanding performance'
            },
            {
                'grade': 'B2',
                'min_score': 75.00,
                'max_score': 79.99,
                'interpretation': 'Very Good',
                'grade_point': 3.50,
                'is_passing': True,
                'remarks': 'Very good performance'
            },
            {
                'grade': 'B3',
                'min_score': 70.00,
                'max_score': 74.99,
                'interpretation': 'Good',
                'grade_point': 3.00,
                'is_passing': True,
                'remarks': 'Good performance'
            },
            {
                'grade': 'C4',
                'min_score': 65.00,
                'max_score': 69.99,
                'interpretation': 'Credit',
                'grade_point': 2.50,
                'is_passing': True,
                'remarks': 'Satisfactory performance'
            },
            {
                'grade': 'C5',
                'min_score': 60.00,
                'max_score': 64.99,
                'interpretation': 'Credit',
                'grade_point': 2.00,
                'is_passing': True,
                'remarks': 'Fairly satisfactory performance'
            },
            {
                'grade': 'C6',
                'min_score': 55.00,
                'max_score': 59.99,
                'interpretation': 'Credit',
                'grade_point': 1.50,
                'is_passing': True,
                'remarks': 'Acceptable performance'
            },
            {
                'grade': 'D7',
                'min_score': 50.00,
                'max_score': 54.99,
                'interpretation': 'Pass',
                'grade_point': 1.00,
                'is_passing': True,
                'remarks': 'Marginally acceptable'
            },
            {
                'grade': 'E8',
                'min_score': 45.00,
                'max_score': 49.99,
                'interpretation': 'Pass',
                'grade_point': 0.50,
                'is_passing': True,
                'remarks': 'Weak pass'
            },
            {
                'grade': 'F9',
                'min_score': 0.00,
                'max_score': 44.99,
                'interpretation': 'Fail',
                'grade_point': 0.00,
                'is_passing': False,
                'remarks': 'Unacceptable performance'
            },
        ]

        created_count = 0
        updated_count = 0

        for data in grading_data:
            grade_scale, created = GradingScale.objects.update_or_create(
                grade=data['grade'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created grade: {grade_scale.grade} ({grade_scale.interpretation})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated grade: {grade_scale.grade} ({grade_scale.interpretation})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Grading scale setup complete! Created: {created_count}, Updated: {updated_count}'
            )
        )

        # Set up default assessment types
        self.stdout.write('\nSetting up default assessment types...')

        assessment_types = [
            {
                'name': 'Class Test',
                'code': 'CT',
                'description': 'Regular class tests',
                'is_exam': False,
                'default_weight': 5.00,
                'default_max_score': 100,
            },
            {
                'name': 'Assignment',
                'code': 'ASG',
                'description': 'Homework and assignments',
                'is_exam': False,
                'default_weight': 5.00,
                'default_max_score': 100,
            },
            {
                'name': 'Quiz',
                'code': 'QZ',
                'description': 'Short quizzes',
                'is_exam': False,
                'default_weight': 5.00,
                'default_max_score': 20,
            },
            {
                'name': 'Project',
                'code': 'PROJ',
                'description': 'Projects and practical work',
                'is_exam': False,
                'default_weight': 10.00,
                'default_max_score': 100,
            },
            {
                'name': 'Mid-Term Exam',
                'code': 'MID',
                'description': 'Mid-term examination',
                'is_exam': False,
                'default_weight': 15.00,
                'default_max_score': 100,
            },
            {
                'name': 'End of Term Exam',
                'code': 'EXAM',
                'description': 'Final end of term examination',
                'is_exam': True,
                'default_weight': 70.00,
                'default_max_score': 100,
            },
        ]

        assessment_created = 0
        assessment_updated = 0

        for data in assessment_types:
            assessment, created = AssessmentType.objects.update_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                assessment_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created assessment type: {assessment.name} ({assessment.code})')
                )
            else:
                assessment_updated += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated assessment type: {assessment.name} ({assessment.code})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Assessment types setup complete! Created: {assessment_created}, Updated: {assessment_updated}'
            )
        )

        self.stdout.write(
            self.style.SUCCESS('\n========================================')
        )
        self.stdout.write(
            self.style.SUCCESS('✓ Grading system setup completed successfully!')
        )
        self.stdout.write(
            self.style.SUCCESS('========================================\n')
        )
