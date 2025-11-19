from django.core.management.base import BaseCommand
from django.db import connection
from schools.models import PlatformUser


class Command(BaseCommand):
    help = 'Create a platform superuser in the public schema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the superuser',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Do not prompt for input',
        )

    def handle(self, *args, **options):
        # Ensure we're in the public schema
        connection.set_schema_to_public()
        
        email = options.get('email')
        password = options.get('password')
        noinput = options.get('noinput')

        # Interactive mode
        if not noinput:
            if not email:
                email = input('Email address: ')
            if not password:
                import getpass
                password = getpass.getpass('Password: ')
                password_confirm = getpass.getpass('Password (again): ')
                
                if password != password_confirm:
                    self.stdout.write(
                        self.style.ERROR('Passwords do not match. Aborting.')
                    )
                    return

        # Validate inputs
        if not email:
            self.stdout.write(
                self.style.ERROR('Email is required')
            )
            return

        if not password:
            self.stdout.write(
                self.style.ERROR('Password is required')
            )
            return

        # Check if user already exists
        if PlatformUser.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email "{email}" already exists')
            )
            return

        # Create the superuser
        try:
            user = PlatformUser.objects.create_superuser(
                email=email,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Platform superuser created successfully!'
                    f'\n   Email: {email}'
                    f'\n   Schema: public'
                    f'\n\nYou can now login at: http://localhost:8000/admin/'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )