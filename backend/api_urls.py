from django.urls import path
from . import api_views

urlpatterns = [
    # Essential API endpoints
    path('home/', api_views.home_api, name='api_home'),
    path('auth/check/', api_views.auth_check_api, name='api_auth_check'),
    path('auth/login/', api_views.login_api, name='api_login'),
    path('auth/register/', api_views.register_api, name='api_register'),
    path('auth/logout/', api_views.logout_api, name='api_logout'),
    
    # Frontend compatibility endpoints (same functions, different URLs)
    path('check_auth/', api_views.auth_check_api, name='api_check_auth'),
    path('login/', api_views.login_api, name='api_login_compat'),
    path('doctor_appointments/', api_views.doctor_appointments_api, name='api_doctor_appointments_compat'),
    
    # Data endpoints
    path('doctors/', api_views.doctors_api, name='api_doctors'),
    path('services/', api_views.services_api, name='api_services'),
    path('appointments/', api_views.appointments_api, name='api_appointments'),
    path('doctor/appointments/', api_views.doctor_appointments_api, name='api_doctor_appointments'),
    path('appointments/<int:appointment_id>/update_status/', api_views.update_appointment_status_api, name='api_update_appointment_status'),
    path('csrf-token/', api_views.csrf_token_api, name='api_csrf_token'),
    
    # Contact form
    path('contact/', api_views.contact_api, name='api_contact'),
]