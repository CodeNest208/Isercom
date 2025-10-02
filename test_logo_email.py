#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isercom_website.settings')
django.setup()

from backend.email_utils import send_email_with_inline_logo

def test_logo_email():
    """Test sending an email with logo attachment"""
    subject = "Test: Logo Email with CID Attachment"
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Logo Test Email</title>
    </head>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
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
            
            <h1 style="color: #667eea;">Logo Attachment Test</h1>
            <p>This is a test email to check if the logo displays correctly using CID attachment.</p>
            <p><strong>If you see the Isercom Clinic logo above, the CID attachment is working!</strong></p>
            <p>If you see the blue box with "🏥 Isercom Clinic" instead, the logo attachment failed but the fallback is working.</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px;">
                Test email from Isercom Clinic System
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_content = """
    Logo Attachment Test
    
    This is a test email to check if the logo displays correctly using CID attachment.
    
    Test email from Isercom Clinic System
    """
    
    # Test email address - replace with your email
    test_email = "test@example.com"  # Change this to your email for testing
    
    print(f"Sending test email with logo attachment to: {test_email}")
    print("Note: Change the test_email variable to your actual email address to receive the test.")
    
    try:
        result = send_email_with_inline_logo(
            subject=subject,
            html_content=html_content,
            plain_content=plain_content,
            recipient_email=test_email,
            async_send=False  # Send synchronously for testing
        )
        
        if result:
            print("✅ Test email sent successfully!")
            print("Check your email inbox to see if the logo displays correctly.")
        else:
            print("❌ Failed to send test email.")
            
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_logo_email()
