from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import base64
import os

# Set up logging for email operations
logger = logging.getLogger(__name__)

# Create a thread pool for async email sending
email_executor = ThreadPoolExecutor(max_workers=3)

def get_logo_for_email():
    """
    Get the Isercom logo for email embedding
    Returns either a base64 encoded image or a static URL
    """
    try:
        # Try multiple paths for the logo
        logo_paths = [
            'images/logo.png',
            'frontend/images/logo.png',
            'staticfiles/images/logo.png'
        ]
        
        logo_path = None
        for path in logo_paths:
            found_path = finders.find(path)
            if found_path:
                # Handle the case where finders.find returns a list
                if isinstance(found_path, list) and found_path:
                    logo_path = found_path[0]
                else:
                    logo_path = found_path
                break
        
        # Also try direct file paths as fallback
        if not logo_path:
            fallback_paths = [
                os.path.join(settings.BASE_DIR, 'frontend', 'images', 'logo.png'),
                os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'logo.png'),
            ]
            for path in fallback_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
        
        if logo_path and isinstance(logo_path, str) and os.path.exists(logo_path):
            logger.info(f"Found logo at: {logo_path}")
            
            # Use base64 encoding for email compatibility (works in most email clients)
            try:
                with open(logo_path, 'rb') as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    logger.info("Successfully encoded logo as base64 for email")
                    return f"data:image/png;base64,{encoded_string}"
            except Exception as e:
                logger.error(f"Could not encode logo as base64: {e}")
        else:
            logger.warning("Logo file not found in any expected location")
            
    except Exception as e:
        logger.error(f"Error in get_logo_for_email: {e}")
    
    # Fallback: return hospital emoji
    logger.info("Using emoji fallback for logo")
    return "🏥"

def get_logo_html(alt_text="Isercom Clinic", use_cid=False):
    """
    Get HTML for the logo in emails as a header with multiple fallbacks
    """
    if use_cid:
        # Use Content-ID for email attachments (better email client support)
        return f'''
        <div style="text-align: center; margin-bottom: 30px; padding: 20px 0; border-bottom: 2px solid #667eea;">
            <div style="display: inline-block; position: relative;">
                <img src="cid:clinic_logo" alt="{alt_text}" 
                     style="height: 80px; max-width: 300px; object-fit: contain; display: block;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <div style="display: none; background: #667eea; color: white; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold;">
                    🏥 {alt_text}
                </div>
            </div>
        </div>
        '''
    
    logo_src = get_logo_for_email()
    
    # If it's base64 or URL, return img tag with fallbacks
    if logo_src.startswith('data:') or logo_src.startswith('http'):
        return f'''
        <div style="text-align: center; margin-bottom: 30px; padding: 20px 0; border-bottom: 2px solid #667eea;">
            <div style="display: inline-block; position: relative;">
                <img src="{logo_src}" alt="{alt_text}" 
                     style="height: 80px; max-width: 300px; object-fit: contain; display: block;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                <div style="display: none; background: #667eea; color: white; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold;">
                    🏥 {alt_text}
                </div>
            </div>
        </div>
        '''
    else:
        # Enhanced fallback with clinic branding
        return f'''
        <div style="text-align: center; margin-bottom: 30px; padding: 20px 0; border-bottom: 2px solid #667eea;">
            <div style="background: #667eea; color: white; padding: 20px; border-radius: 10px; display: inline-block; font-size: 24px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                🏥 {alt_text}
            </div>
        </div>
        '''

def get_email_settings():
    """Get email configuration with fallbacks"""
    return {
        'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@isercomclinic.com'),
        'backend': getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
    }

def send_email_with_inline_logo(subject, html_content, plain_content, recipient_email, sender_email=None, async_send=True):
    """
    Send email with logo properly embedded inline in the header using CID
    """
    from django.core.mail import EmailMessage
    from email.mime.image import MIMEImage
    import os
    
    def _send_email():
        try:
            email_config = get_email_settings()
            from_email = sender_email or email_config['from_email']
            
            # Create Django EmailMessage
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=from_email,
                to=[recipient_email]
            )
            
            # Set content type to HTML
            email.content_subtype = 'html'
            
            # Try to attach logo as inline image
            logo_paths = [
                os.path.join(settings.BASE_DIR, 'frontend', 'images', 'logo.png'),
                os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'),
                os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'logo.png'),
            ]
            
            logo_attached = False
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    try:
                        with open(logo_path, 'rb') as f:
                            logo_data = f.read()
                        
                        # Attach the image with CID - need to modify message after creation
                        email.attach('logo.png', logo_data, 'image/png')
                        
                        # Custom hook to modify message structure for CID
                        original_message = email.message
                        def custom_message():
                            msg = original_message()
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if (part.get_content_type() == 'image/png' and 
                                        part.get_filename() == 'logo.png'):
                                        part.add_header('Content-ID', '<clinic_logo>')
                                        part.replace_header('Content-Disposition', 'inline; filename="logo.png"')
                                        break
                            return msg
                        
                        # Replace the message method temporarily
                        email.message = custom_message
                        
                        logo_attached = True
                        logger.info(f"Logo embedded inline from: {logo_path}")
                        break
                        
                    except Exception as e:
                        logger.warning(f"Failed to embed logo from {logo_path}: {str(e)}")
                        continue
            
            if not logo_attached:
                logger.warning("No logo could be embedded - HTML will show fallback text")
            
            # Send the email
            start_time = time.time()
            result = email.send()
            end_time = time.time()
            
            if result:
                logger.info(f"Email with inline logo sent successfully to {recipient_email} in {end_time - start_time:.2f}s")
                return True
            else:
                logger.error(f"Failed to send email with inline logo to {recipient_email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email with inline logo to {recipient_email}: {str(e)}")
            return False
    
    if async_send:
        try:
            future = email_executor.submit(_send_email)
            logger.info(f"Email with inline logo queued for async sending to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue email with inline logo for {recipient_email}: {str(e)}")
            return False
    else:
        return _send_email()

def send_email_with_logo_attachment(subject, html_content, plain_content, recipient_email, sender_email=None, async_send=True):
    """
    Send email with logo as CID attachment for better email client compatibility
    """
    from django.core.mail import EmailMultiAlternatives
    from email.mime.image import MIMEImage
    import os
    
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
            msg.attach_alternative(html_content, "text/html")
            
            # Try to attach logo as CID
            logo_paths = [
                os.path.join(settings.BASE_DIR, 'frontend', 'images', 'logo.png'),
                os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'),
                os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'logo.png'),
            ]
            
            logo_attached = False
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    try:
                        with open(logo_path, 'rb') as f:
                            logo_data = f.read()
                        
                        # Attach logo as file attachment with CID
                        msg.attach('logo.png', logo_data, 'image/png')
                        
                        # Set Content-ID for the attachment
                        # This requires accessing the underlying email structure
                        if hasattr(msg, 'message'):
                            email_msg = msg.message()
                            if email_msg.is_multipart():
                                for part in email_msg.get_payload():
                                    if part.get_filename() == 'logo.png':
                                        part.add_header('Content-ID', '<clinic_logo>')
                                        part.add_header('Content-Disposition', 'inline; filename="logo.png"')
                                        break
                        logo_attached = True
                        logger.info(f"Logo attached as CID from: {logo_path}")
                        break
                        
                    except Exception as e:
                        logger.warning(f"Failed to attach logo from {logo_path}: {str(e)}")
                        continue
            
            if not logo_attached:
                logger.warning("No logo could be attached to email - using fallback text")
            
            # Send email with timeout
            start_time = time.time()
            result = msg.send()
            end_time = time.time()
            
            if result:
                logger.info(f"Email with logo attachment sent successfully to {recipient_email} in {end_time - start_time:.2f}s")
                return True
            else:
                logger.error(f"Failed to send email with logo attachment to {recipient_email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email with logo attachment to {recipient_email}: {str(e)}")
            return False
    
    if async_send:
        # Send email asynchronously to avoid blocking the main thread
        try:
            future = email_executor.submit(_send_email)
            logger.info(f"Email with logo attachment queued for async sending to {recipient_email}")
            return True  # Return immediately for async sending
        except Exception as e:
            logger.error(f"Failed to queue email with logo attachment for {recipient_email}: {str(e)}")
            return False
    else:
        # Send email synchronously
        return _send_email()

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
        
        # Get logo for email header
        logo_html = get_logo_html("Isercom Clinic", use_cid=True)
        
        # Email subject
        subject = f'New Appointment Booked - {patient_name}'
        
        # Email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {logo_html}
                
                <h2 style="color: #667eea; margin-top: 0;">
                    New Appointment Notification
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
        
        # Send email using the inline logo function
        return send_email_with_inline_logo(
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
        
        # Get logo for email header
        logo_html = get_logo_html("Isercom Clinic", use_cid=True)
        
        # Email subject
        subject = f'Appointment Confirmation - Isercom Clinic'
        
        # Email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {logo_html}
                
                <h2 style="color: #667eea; margin-top: 0;">
                    Appointment Confirmation
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
        
        # Send email using the inline logo function
        return send_email_with_inline_logo(
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

def send_appointment_reminder_to_patient(appointment, async_send=True):
    """
    Send appointment reminder email to patient one hour before appointment
    """
    try:
        patient_email = appointment.patient.email
        patient_name = appointment.patient.full_name
        doctor_name = appointment.doctor.full_name
        appointment_date = appointment.date.strftime('%B %d, %Y')
        appointment_time = appointment.time.strftime('%I:%M %p')
        service_name = appointment.service.name
        
        # Prepare email content
        subject = f"⏰ Appointment Reminder - {appointment_date} at {appointment_time}"
        
        # HTML message with professional styling
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Appointment Reminder</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
            {get_logo_html(use_cid=True)}
            
            <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #667eea; margin: 0; font-size: 28px;">⏰ Appointment Reminder</h1>
                    <p style="color: #666; font-size: 16px; margin: 10px 0 0 0;">Your appointment is in 1 hour</p>
                </div>

                <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <h2 style="color: #667eea; margin: 0 0 15px 0; font-size: 20px;">Dear {patient_name},</h2>
                    <p style="margin: 0 0 15px 0; font-size: 16px; color: #555;">
                        This is a friendly reminder that you have an upcoming appointment scheduled with <strong>{doctor_name}</strong>.
                    </p>
                </div>

                <div style="background: #fff8f0; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #ffeaa7;">
                    <h3 style="color: #e17055; margin: 0 0 15px 0; font-size: 18px;">📅 Appointment Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666; width: 30%;">Date:</td>
                            <td style="padding: 8px 0; color: #333;">{appointment_date}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Time:</td>
                            <td style="padding: 8px 0; color: #333;">{appointment_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Doctor:</td>
                            <td style="padding: 8px 0; color: #333;">{doctor_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold; color: #666;">Service:</td>
                            <td style="padding: 8px 0; color: #333;">{service_name}</td>
                        </tr>
                    </table>
                </div>

                <div style="background: #e8f6f3; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #00cec9;">
                    <h3 style="color: #00b894; margin: 0 0 15px 0; font-size: 18px;">💡 Preparation Tips</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #555;">
                        <li style="margin-bottom: 8px;">Please arrive 15 minutes early for check-in</li>
                        <li style="margin-bottom: 8px;">Bring a valid ID and insurance card (if applicable)</li>
                        <li style="margin-bottom: 8px;">Bring any relevant medical records or medications</li>
                        <li style="margin-bottom: 8px;">Prepare a list of questions or concerns you'd like to discuss</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <p style="color: #666; font-size: 14px; margin: 0;">
                        If you need to reschedule or cancel your appointment, please contact us as soon as possible.
                    </p>
                </div>

                <div style="border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px; text-align: center;">
                    <p style="color: #888; font-size: 12px; margin: 5px 0;">
                        Isercom Medical & Fertility Center<br>
                        Providing compassionate healthcare since 2025
                    </p>
                    <p style="color: #999; font-size: 11px; margin: 15px 0 0 0;">
                        This is an automated reminder. Please do not reply to this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
        APPOINTMENT REMINDER
        
        Dear {patient_name},
        
        This is a friendly reminder that you have an upcoming appointment in 1 hour.
        
        APPOINTMENT DETAILS:
        Date: {appointment_date}
        Time: {appointment_time}
        Doctor: {doctor_name}
        Service: {service_name}
        
        PREPARATION TIPS:
        - Please arrive 15 minutes early for check-in
        - Bring a valid ID and insurance card (if applicable)
        - Bring any relevant medical records or medications
        - Prepare a list of questions or concerns you'd like to discuss
        
        If you need to reschedule or cancel your appointment, please contact us as soon as possible.
        
        Best regards,
        iSecorm Medical & Fertility Center
        
        This is an automated reminder. Please do not reply to this email.
        """
        
        # Send the email with inline logo
        logger.info(f"Sending appointment reminder to {patient_email} for appointment on {appointment_date} at {appointment_time}")
        
        return send_email_with_inline_logo(
            subject=subject,
            html_content=html_message,
            plain_content=plain_message,
            recipient_email=patient_email,
            async_send=async_send
        )
        
    except Exception as e:
        logger.error(f"Failed to send appointment reminder: {str(e)}")
        print(f"Reminder Email Error: {str(e)}")
        return False
