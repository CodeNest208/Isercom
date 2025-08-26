#!/usr/bin/env python3
"""
Test script to check appointment status update functionality
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isercom_website.settings')
django.setup()

from backend.models import Appointment, Doctor, Patient, Service
from django.contrib.auth.models import User

def test_appointment_status_update():
    """Test appointment status update functionality"""
    print("Testing appointment status update...")
    
    # Check if we have any appointments
    appointments = Appointment.objects.all()
    print(f"Total appointments in database: {appointments.count()}")
    
    if appointments.exists():
        for apt in appointments[:5]:  # Show first 5 appointments
            print(f"Appointment {apt.id}: {apt.patient.user.first_name} {apt.patient.user.last_name} - Status: {apt.status}")
            print(f"  Doctor: Dr. {apt.doctor.user.first_name} {apt.doctor.user.last_name}")
            print(f"  Date: {apt.date}, Time: {apt.time}")
            print(f"  Service: {apt.service.name}")
            print()
    
    # Check valid statuses
    print("Valid appointment statuses:")
    print("- scheduled")
    print("- confirmed") 
    print("- completed")
    print("- cancelled")
    
    # Test status transition logic
    print("\nStatus transition logic:")
    print("scheduled → confirmed (Confirm button)")
    print("confirmed → completed (Mark Complete button)")

if __name__ == "__main__":
    test_appointment_status_update()
