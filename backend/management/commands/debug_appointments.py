from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backend.models import Patient, Doctor, Appointment, Service
from datetime import date, time

class Command(BaseCommand):
    help = 'Test appointments data and create sample appointments if needed'

    def handle(self, *args, **options):
        self.stdout.write("=== Appointments Debug Command ===")
        
        # Check all users
        users = User.objects.all()
        self.stdout.write(f"Total users: {users.count()}")
        
        # Check all patients
        patients = Patient.objects.all()
        self.stdout.write(f"Total patients: {patients.count()}")
        
        # Check all doctors
        doctors = Doctor.objects.all()
        self.stdout.write(f"Total doctors: {doctors.count()}")
        
        # Check all services
        services = Service.objects.all()
        self.stdout.write(f"Total services: {services.count()}")
        
        # Check all appointments
        appointments = Appointment.objects.all()
        self.stdout.write(f"Total appointments: {appointments.count()}")
        
        # List patients and their appointments
        for patient in patients:
            patient_appointments = Appointment.objects.filter(patient=patient)
            self.stdout.write(f"Patient: {patient.user.username} ({patient.user.get_full_name()}) - Appointments: {patient_appointments.count()}")
            for apt in patient_appointments:
                self.stdout.write(f"  - {apt.date} {apt.time} - {apt.status} - Dr. {apt.doctor.full_name}")
        
        # Create sample appointment if none exist and we have the required data
        if appointments.count() == 0 and patients.count() > 0 and doctors.count() > 0 and services.count() > 0:
            self.stdout.write("Creating sample appointment...")
            patient = patients.first()
            doctor = doctors.first()
            service = services.first()
            
            sample_appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                service=service,
                date=date.today(),
                time=time(14, 30),  # 2:30 PM
                status='scheduled',
                notes='Sample appointment for testing'
            )
            self.stdout.write(f"Created sample appointment: {sample_appointment}")
        
        self.stdout.write("=== Debug Complete ===")
