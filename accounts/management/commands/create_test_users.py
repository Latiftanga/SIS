"""
Django Management Command: Create Test Users for SmartSIS

INSTALLATION:
1. Save this file to: accounts/management/commands/create_test_users.py
2. Ensure __init__.py files exist in:
   - accounts/management/__init__.py
   - accounts/management/commands/__init__.py
3. Run: python manage.py create_test_users

USAGE:
    python manage.py create_test_users           # Create test users
    python manage.py create_test_users --delete  # Delete and recreate
    python manage.py create_test_users --help    # Show help
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users for SmartSIS development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete existing test users before creating new ones',
        )

    def handle(self, *args, **options):
        """Main command logic"""
        
        # Test users configuration
        test_users = [
            {
                'email': 'admin@test.com',
                'password': 'testpass123',
                'is_school_admin': True,
                'is_staff': True,
                'role_name': 'School Admin',
            },
            {
                'email': 'teacher@test.com',
                'password': 'testpass123',
                'is_teacher': True,
                'role_name': 'Teacher',
            },
            {
                'email': 'student@test.com',
                'password': 'testpass123',
                'is_student': True,
                'role_name': 'Student',
            },
            {
                'email': 'parent@test.com',
                'password': 'testpass123',
                'is_parent': True,
                'role_name': 'Parent',
            },
        ]

        # Delete existing test users if --delete flag is used
        if options['delete']:
            self.stdout.write(
                self.style.WARNING('Deleting existing test users...')
            )
            for user_data in test_users:
                deleted_count = User.objects.filter(
                    email=user_data['email']
                ).delete()[0]
                if deleted_count > 0:
                    self.stdout.write(f'  ✓ Deleted {user_data["email"]}')
            self.stdout.write(
                self.style.SUCCESS('✓ Cleanup complete\n')
            )

        # Create test users
        self.stdout.write(
            self.style.MIGRATE_HEADING('Creating test users...\n')
        )
        
        created_count = 0
        skipped_count = 0
        
        for user_data in test_users:
            email = user_data.pop('email')
            password = user_data.pop('password')
            role_name = user_data.pop('role_name')
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ User {email} already exists, skipping...'
                    )
                )
                skipped_count += 1
                continue
            
            # Create the user
            try:
                # Use the appropriate manager method based on role
                if user_data.get('is_school_admin'):
                    user = User.objects.create_school_admin(
                        email=email,
                        password=password
                    )
                elif user_data.get('is_teacher'):
                    user = User.objects.create_teacher(
                        email=email,
                        password=password
                    )
                elif user_data.get('is_student'):
                    user = User.objects.create_student(
                        email=email,
                        password=password
                    )
                elif user_data.get('is_parent'):
                    user = User.objects.create_parent(
                        email=email,
                        password=password
                    )
                else:
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        **user_data
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created {role_name}: {email}'
                    )
                )
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Failed to create {email}: {str(e)}'
                    )
                )

        # Summary
        self.stdout.write('\n' + '=' * 60)
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Successfully created {created_count} test user(s)!'
                )
            )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Skipped {skipped_count} existing user(s)'
                )
            )
        self.stdout.write('=' * 60)
        
        # Instructions
        if created_count > 0:
            self.stdout.write('\n' + self.style.MIGRATE_LABEL('Next Steps:'))
            self.stdout.write('1. Run: python manage.py runserver')
            self.stdout.write('2. Visit: http://127.0.0.1:8000/')
            self.stdout.write('3. Login with any of these accounts:\n')
            
            self.stdout.write(
                self.style.SUCCESS('   School Admin: admin@test.com / testpass123')
            )
            self.stdout.write(
                self.style.SUCCESS('   Teacher:      teacher@test.com / testpass123')
            )
            self.stdout.write(
                self.style.SUCCESS('   Student:      student@test.com / testpass123')
            )
            self.stdout.write(
                self.style.SUCCESS('   Parent:       parent@test.com / testpass123')
            )
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(
                self.style.WARNING(
                    '\nNote: These users only have email/password. '
                    'Create Teacher/Student/Parent profiles to add names and other details.'
                )
            )
            self.stdout.write('=' * 60)