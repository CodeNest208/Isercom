from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backend.models import Patient, Doctor, Service, Appointment
from datetime import date, time, timedelta


class Command(BaseCommand):
    help = 'Create test data for the clinic system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data...'))

        # Create services
        services_data = [
            {'name': 'General Consultation', 'description': 'General medical consultation and health check-up'},
            {'name': 'Fertility Consultation', 'description': 'Specialized fertility and reproductive health consultation'},
            {'name': 'Prenatal Care', 'description': 'Comprehensive prenatal care for expectant mothers'},
            {'name': 'Gynecological Exam', 'description': 'Routine gynecological examination and screening'},
            {'name': 'Family Planning', 'description': 'Family planning and contraceptive counseling'},
        ]

        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={'description': service_data['description']}
            )
            if created:
                self.stdout.write(f'Created service: {service.name}')

        # Create test doctor
        doctor_user_data = {
            'username': 'doctor1',
            'email': 'doctor@isercom.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'password': 'testpass123'
        }

        doctor_user, created = User.objects.get_or_create(
            email=doctor_user_data['email'],
            defaults=doctor_user_data
        )
        
        if created:
            doctor_user.set_password(doctor_user_data['password'])
            doctor_user.save()
            self.stdout.write(f'Created doctor user: {doctor_user.email}')

        doctor, created = Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={
                'speciality': 'Fertility and Reproductive Medicine',
                'phone': '+1234567890',
                'address': '123 Medical Center Drive',
                'license_number': 'MD12345'
            }
        )
        
        if created:
            self.stdout.write(f'Created doctor: Dr. {doctor.full_name}')

        # Create test patient
        patient_user_data = {
            'username': 'patient1',
            'email': 'patient@test.com',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'password': 'testpass123'
        }

        patient_user, created = User.objects.get_or_create(
            email=patient_user_data['email'],
            defaults=patient_user_data
        )
        
        if created:
            patient_user.set_password(patient_user_data['password'])
            patient_user.save()
            self.stdout.write(f'Created patient user: {patient_user.email}')

        patient, created = Patient.objects.get_or_create(
            user=patient_user,
            defaults={
                'phone': '+0987654321',
                'date_of_birth': date(1990, 5, 15),
                'address': '456 Patient Street'
            }
        )
        
        if created:
            self.stdout.write(f'Created patient: {patient.full_name}')

        self.stdout.write(self.style.SUCCESS('Test data creation completed!'))
        self.stdout.write('')
        self.stdout.write('Test credentials:')
        self.stdout.write(f'Doctor: doctor@isercom.com / testpass123')
        self.stdout.write(f'Patient: patient@test.com / testpass123')