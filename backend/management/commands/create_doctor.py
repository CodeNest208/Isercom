from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backend.models import Doctor


class Command(BaseCommand):
    help = 'Create a doctor user account'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the doctor')
        parser.add_argument('--email', type=str, help='Email for the doctor')
        parser.add_argument('--first_name', type=str, help='First name')
        parser.add_argument('--last_name', type=str, help='Last name')
        parser.add_argument('--speciality', type=str, help='Doctor speciality')
        parser.add_argument('--phone', type=str, help='Phone number')
        parser.add_argument('--license_number', type=str, help='License number')
        parser.add_argument('--password', type=str, help='Password (optional, will prompt if not provided)')

    def handle(self, *args, **options):
        username = options['username'] or input('Username: ')
        email = options['email'] or input('Email: ')
        first_name = options['first_name'] or input('First name: ')
        last_name = options['last_name'] or input('Last name: ')
        speciality = options['speciality'] or input('Speciality: ')
        phone = options['phone'] or input('Phone: ')
        license_number = options['license_number'] or input('License number (optional): ')
        
        if options['password']:
            password = options['password']
        else:
            import getpass
            password = getpass.getpass('Password: ')

        try:
            # Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Create Doctor profile
            doctor = Doctor.objects.create(
                user=user,
                speciality=speciality,
                phone=phone,
                license_number=license_number if license_number else None
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created doctor: {doctor.full_name} (Username: {username})'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating doctor: {str(e)}')
            )
