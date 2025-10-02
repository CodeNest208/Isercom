#!/usr/bin/env python
"""
Complete test of the email system with inline logos
Tests all three email types: doctor notification, patient confirmation, reminder
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isercom_website.settings')
django.setup()

from backend.email_utils import (
    send_email_with_inline_logo, 
    send_appointment_notification_to_doctor,
    send_appointment_confirmation_to_patient,
    send_appointment_reminder_to_patient
)
from backend.models import Patient, Doctor, Service, Appointment
from django.contrib.auth.models import User

def test_inline_logo_email():
    """Test basic inline logo email functionality"""
    print("🧪 Testing basic inline logo email...")
    
    # Test email (change to your actual email to receive test)
    test_email = "test@example.com"  # Change this to your actual email
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Logo Test</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <!-- Logo Header -->
        <div style="text-align: center; margin-bottom: 30px; padding: 20px 0; border-bottom: 2px solid #667eea;">
            <div style="display: inline-block; position: relative;">
                <img src="cid:clinic_logo" alt="Isercom Clinic" 
                     style="height: 80px; max-width: 300px; object-fit: contain; display: block;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <div style="display: none; background: #667eea; color: white; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold;">
                    🏥 Isercom Clinic
                </div>
            </div>
        </div>
        
        <!-- Email Body -->
        <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h1 style="color: #667eea;">✅ Email Logo Test</h1>
            <p>This is a test email to verify that the Isercom Clinic logo displays correctly as an inline header.</p>
            
            <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 20px 0;">
                <h3 style="color: #667eea; margin-top: 0;">What you should see:</h3>
                <ul>
                    <li>The Isercom Clinic logo at the top of this email (not as a separate attachment)</li>
                    <li>This styled content below the logo</li>
                    <li>Professional email formatting</li>
                </ul>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_content = f"""
    EMAIL LOGO TEST
    
    This is a test email to verify that the Isercom Clinic logo displays correctly.
    
    What you should see:
    - The Isercom Clinic logo at the top of this email (not as a separate attachment)
    - This styled content below the logo
    - Professional email formatting
    
    Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    try:
        result = send_email_with_inline_logo(
            subject="🧪 Email Logo Test - Inline Header Display",
            html_content=html_content,
            plain_content=plain_content,
            recipient_email=test_email,
            async_send=False  # Synchronous for testing
        )
        
        if result:
            print(f"✅ Basic inline logo email sent successfully to {test_email}")
            print("📧 Check your email inbox to verify the logo displays inline at the header")
            return True
        else:
            print("❌ Failed to send basic inline logo email")
            return False
            
    except Exception as e:
        print(f"❌ Error sending basic inline logo email: {str(e)}")
        return False

def test_appointment_emails():
    """Test appointment-related emails with inline logos"""
    print("\n🏥 Testing appointment email system...")
    
    try:
        # Get or create test data
        print("Setting up test data...")
        
        # Create test user and patient
        test_user, created = User.objects.get_or_create(
            username='test_patient',
            defaults={
                'email': 'test.patient@example.com',  # Change to your email
                'first_name': 'Test',
                'last_name': 'Patient'
            }
        )
        
        test_patient, created = Patient.objects.get_or_create(
            user=test_user,
            defaults={'phone': '555-0123'}
        )
        
        # Create test doctor user
        doctor_user, created = User.objects.get_or_create(
            username='test_doctor',
            defaults={
                'email': 'test.doctor@example.com',  # Change to your email
                'first_name': 'Test',
                'last_name': 'Doctor'
            }
        )
        
        test_doctor, created = Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={'speciality': 'General Practice', 'qualification': 'MD'}
        )
        
        # Create test service
        test_service, created = Service.objects.get_or_create(
            name='Test Consultation',
            defaults={'description': 'Test consultation service', 'price': 100.00}
        )
        
        # Create test appointment
        appointment_date = datetime.now().date() + timedelta(days=1)
        appointment_time = datetime.now().time().replace(hour=14, minute=0, second=0, microsecond=0)
        
        test_appointment, created = Appointment.objects.get_or_create(
            patient=test_patient,
            doctor=test_doctor,
            service=test_service,
            date=appointment_date,
            time=appointment_time,
            defaults={
                'status': 'scheduled',
                'reminder_sent': False,
                'notes': 'Test appointment for email system'
            }
        )
        
        print(f"Test appointment created: {test_appointment.pk if test_appointment else 'None'}")
        
        # Test doctor notification email
        print("Testing doctor notification email...")
        doctor_result = send_appointment_notification_to_doctor(test_appointment, async_send=False)
        
        # Test patient confirmation email
        print("Testing patient confirmation email...")
        patient_result = send_appointment_confirmation_to_patient(test_appointment, async_send=False)
        
        # Test reminder email
        print("Testing appointment reminder email...")
        reminder_result = send_appointment_reminder_to_patient(test_appointment, async_send=False)
        
        # Results
        if doctor_result and patient_result and reminder_result:
            print("✅ All appointment emails sent successfully!")
            print("📧 Check your email inbox to verify all logos display inline at the headers")
            return True
        else:
            print(f"⚠️  Some emails failed: Doctor={doctor_result}, Patient={patient_result}, Reminder={reminder_result}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing appointment emails: {str(e)}")
        return False

def main():
    """Run all email tests"""
    print("🚀 Starting complete email system test with inline logos...")
    print("="*60)
    
    # Test 1: Basic inline logo email
    basic_test = test_inline_logo_email()
    
    # Test 2: Appointment emails
    appointment_test = test_appointment_emails()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY:")
    print(f"✅ Basic inline logo email: {'PASSED' if basic_test else 'FAILED'}")
    print(f"✅ Appointment email system: {'PASSED' if appointment_test else 'FAILED'}")
    
    if basic_test and appointment_test:
        print("\n🎉 ALL TESTS PASSED!")
        print("💡 The email system is working correctly with inline logos.")
        print("📧 Check your email inbox to verify the logos display in the headers (not as attachments).")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔧 Check the Django settings and email configuration.")
    
    print("\nNote: Make sure to change the test email addresses in this script to your actual email to receive the test emails.")

if __name__ == "__main__":
    main()
