from django.urls import path, include, re_path
from django.shortcuts import redirect
from django.http import FileResponse, Http404
from django.conf import settings
import os
import mimetypes

from . import views

def serve_frontend_file(request, file_path='index.html'):
    """Serve frontend files with proper MIME types"""
    # Handle root frontend request
    if not file_path or file_path == '':
        file_path = 'index.html'
    
    # Construct full file path
    full_path = os.path.join(settings.BASE_DIR, 'frontend', file_path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        raise Http404(f"Frontend file not found: {file_path}")
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(full_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    # Return file response
    return FileResponse(open(full_path, 'rb'), content_type=mime_type)

urlpatterns = [
    path('', lambda request: serve_frontend_file(request, 'index.html'), name='home'),
    # Frontend file serving with flexible paths
    re_path(r'^frontend/(?P<file_path>.*)$', serve_frontend_file, name='frontend_files'),
    path('admin_home/', views.home, name='admin_home'),  # Original admin home
    path('appointment_form/',views.create_appointment,name='create_appointment'),
    path('appointment_success/',views.appointment_success,name='appointment_success'),
    path('my_appointments/',views.my_appointments,name='my_appointments'),
    path('register/', views.register, name='register'),
    path('doctor_dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patient_dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor_appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('update_appointment_status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
    
    # Static frontend pages
    path('about/', views.about_us, name='about_us'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('faq/', views.faq, name='faq'),
    path('gynaecology/', views.gynaecology, name='gynaecology'),
    path('fertility/',views.fertility,name='fertility'),
    path('antenatal/',views.antenatal, name='antenatal'),
    path('consultation/',views.consultation,name='consultation'),
]