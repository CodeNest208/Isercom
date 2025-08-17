from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Set up logging for email operations
logger = logging.getLogger(__name__)

# Create a thread pool for async email sending
email_executor = ThreadPoolExecutor(max_workers=3)

def get_email_settings():
    """Get email configuration with fallbacks"""
    return {
        'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@isercomclinic.com'),
        'backend': getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
    }

def send_email_safely(subject, html_content, plain_content, recipient_email, sender_email=None, async_send=True):
    """
    Safely send email with proper error handling and optional async sending
    """
    def _send_email():
        try:
            email_config = get_email_settings()
            from_email = sender_email or email_config['from_email']
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_content,
                from_email=from_email,
                to=[recipient_email]
            )
            
            # Attach HTML alternative
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            
            # Send email with timeout
            start_time = time.time()
            result = msg.send()
            end_time = time.time()
            
            if result:
                logger.info(f"Email sent successfully to {recipient_email} in {end_time - start_time:.2f}s")
                return True
            else:
                logger.error(f"Failed to send email to {recipient_email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {str(e)}")
            print(f"Email Error: {str(e)}")  # Also print for immediate feedback
            return False
    
    if async_send:
        # Send email asynchronously to avoid blocking the main thread
        try:
            future = email_executor.submit(_send_email)
            logger.info(f"Email queued for async sending to {recipient_email}")
            return True  # Return immediately for async sending
        except Exception as e:
            logger.error(f"Failed to queue email for {recipient_email}: {str(e)}")
            return False
    else:
        # Send email synchronously
        return _send_email()

def send_appointment_emails_async(appointment):
    """
    Send both doctor notification and patient confirmation emails asynchronously
    Returns immediately without waiting for emails to be sent
    """
    try:
        # Queue both emails for async sending
        doctor_queued = send_appointment_notification_to_doctor(appointment, async_send=True)
        patient_queued = send_appointment_confirmation_to_patient(appointment, async_send=True)
        
        if doctor_queued and patient_queued:
            logger.info(f"Both appointment emails queued for appointment {appointment.id}")
            return True, "Emails are being sent in the background"
        elif doctor_queued:
            logger.warning(f"Only doctor email queued for appointment {appointment.id}")
            return True, "Doctor notification is being sent"
        elif patient_queued:
            logger.warning(f"Only patient email queued for appointment {appointment.id}")
            return True, "Patient confirmation is being sent"
        else:
            logger.error(f"Failed to queue emails for appointment {appointment.id}")
            return False, "Failed to queue emails"
            
    except Exception as e:
        logger.error(f"Error queuing appointment emails: {str(e)}")
        return False, f"Error: {str(e)}"

def send_appointment_notification_to_doctor(appointment, async_send=True):
    """
    Send email notification to doctor when a new appointment is booked
    """
    try:
        # Validate appointment and doctor data
        if not appointment or not appointment.doctor or not appointment.doctor.user:
            logger.error("Invalid appointment or doctor data")
            return False
            
        doctor_email = appointment.doctor.user.email
        if not doctor_email:
            logger.error("Doctor email not found")
            return False
        
        # Prepare email data
        patient_name = appointment.patient.full_name if hasattr(appointment.patient, 'full_name') else f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}"
        doctor_first_name = appointment.doctor.user.first_name
        
        # Email subject
        subject = f'New Appointment Booked - {patient_name}'
        
        # Email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                    🏥 New Appointment Notification
                </h2>
                
                <p>Dear Dr. {doctor_first_name},</p>
                
                <p>A new appointment has been booked with you. Here are the details:</p>
                
                <div style="background-color: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #4a5568; margin-top: 0;">Appointment Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 30%;">Patient:</td>
                            <td style="padding: 8px 0;">{patient_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Date:</td>
                            <td style="padding: 8px 0;">{appointment.date}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Time:</td>
                            <td style="padding: 8px 0;">{appointment.time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Service:</td>
                            <td style="padding: 8px 0;">{appointment.service.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Status:</td>
                            <td style="padding: 8px 0; color: #ed8936;">{appointment.status.title()}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #e6fffa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #2d3748; margin-top: 0;">Patient Contact Information</h4>
                    <p style="margin: 5px 0;"><strong>Email:</strong> {appointment.patient.user.email}</p>
                    <p style="margin: 5px 0;"><strong>Phone:</strong> {getattr(appointment.patient, 'phone', 'Not provided')}</p>
                </div>
                
                <p>Please log into your doctor portal to manage this appointment.</p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="color: #718096; font-size: 14px;">
                    This email was sent automatically by the Isercom Clinic booking system.<br>
                    If you have any questions, please contact the clinic administration.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (for email clients that don't support HTML)
        plain_message = f"""
        New Appointment Notification
        
        Dear Dr. {doctor_first_name},
        
        A new appointment has been booked with you:
        
        Patient: {patient_name}
        Date: {appointment.date}
        Time: {appointment.time}
        Service: {appointment.service.name}
        Status: {appointment.status.title()}
        
        Patient Contact:
        Email: {appointment.patient.user.email}
        Phone: {getattr(appointment.patient, 'phone', 'Not provided')}
        
        Please log into your doctor portal to manage this appointment.
        
        This email was sent automatically by the Isercom Clinic booking system.
        """
        
        # Send email using the safe email function
        return send_email_safely(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=doctor_email,
            async_send=async_send
        )
        
    except Exception as e:
        logger.error(f"Failed to send doctor notification: {str(e)}")
        print(f"Doctor Email Error: {str(e)}")
        return False

def send_appointment_confirmation_to_patient(appointment, async_send=True):
    """
    Send confirmation email to patient when appointment is booked
    """
    try:
        # Validate appointment and patient data
        if not appointment or not appointment.patient or not appointment.patient.user:
            logger.error("Invalid appointment or patient data")
            return False
            
        patient_email = appointment.patient.user.email
        if not patient_email:
            logger.error("Patient email not found")
            return False
        
        # Prepare email data
        patient_name = appointment.patient.user.first_name
        doctor_name = appointment.doctor.full_name if hasattr(appointment.doctor, 'full_name') else f"Dr. {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}"
        
        # Email subject
        subject = f'Appointment Confirmation - Isercom Clinic'
        
        # Email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px;">
                    🏥 Appointment Confirmation
                </h2>
                
                <p>Dear {patient_name},</p>
                
                <p>Your appointment has been successfully booked! Here are your appointment details:</p>
                
                <div style="background-color: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #4a5568; margin-top: 0;">Your Appointment</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; width: 30%;">Doctor:</td>
                            <td style="padding: 8px 0;">{doctor_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Specialty:</td>
                            <td style="padding: 8px 0;">{getattr(appointment.doctor, 'speciality', 'General Practice')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Date:</td>
                            <td style="padding: 8px 0;">{appointment.date}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Time:</td>
                            <td style="padding: 8px 0;">{appointment.time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">Service:</td>
                            <td style="padding: 8px 0;">{appointment.service.name}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-top: 0;">Important Reminders</h4>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Please arrive 15 minutes before your appointment time</li>
                        <li>Bring a valid ID and insurance information</li>
                        <li>If you need to cancel or reschedule, please contact us at least 24 hours in advance</li>
                    </ul>
                </div>
                
                <p>If you have any questions or need to make changes, please contact our clinic.</p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="color: #718096; font-size: 14px;">
                    Thank you for choosing Isercom Clinic for your healthcare needs.<br>
                    This email was sent automatically by our booking system.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
        Appointment Confirmation - Isercom Clinic
        
        Dear {patient_name},
        
        Your appointment has been successfully booked!
        
        Doctor: {doctor_name}
        Specialty: {getattr(appointment.doctor, 'speciality', 'General Practice')}
        Date: {appointment.date}
        Time: {appointment.time}
        Service: {appointment.service.name}
        
        Important Reminders:
        - Please arrive 15 minutes before your appointment time
        - Bring a valid ID and insurance information
        - If you need to cancel or reschedule, please contact us at least 24 hours in advance
        
        Thank you for choosing Isercom Clinic for your healthcare needs.
        """
        
        # Send email using the safe email function
        return send_email_safely(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=patient_email,
            async_send=async_send
        )
        
    except Exception as e:
        logger.error(f"Failed to send patient confirmation: {str(e)}")
        print(f"Patient Email Error: {str(e)}")
        return False
