import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import Patient, Doctor, Service, Appointment
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.middleware.csrf import get_token
from .email_utils import send_appointment_emails_async


@require_http_methods(["GET"])
def home_api(request):
    """
    API endpoint for homepage data
    """
    try:
        # Return basic homepage information
        data = {
            'message': 'Welcome to Isercom Clinic',
            'clinic_name': 'Isercom Medical and Fertility Centre',
            'services': [
                'Medical Consultations',
                'Fertility Treatments', 
                'Diagnostic Services',
                'Health Checkups'
            ]
        }
        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading homepage: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def auth_check_api(request):
    """
    Check if user is authenticated and return user info with role
    """
    try:
        if request.user.is_authenticated:
            user = request.user
            user_type = 'user'  # default
            profile_info = {}
            redirect_url = '/frontend/index.html'  # default
            
            # Check if user is a doctor
            try:
                from .models import Doctor
                doctor = Doctor.objects.get(user=user)
                user_type = 'doctor'
                redirect_url = '/frontend/pages/doctor_home.html'
                profile_info = {
                    'full_name': f"Dr. {user.first_name} {user.last_name}",
                    'speciality': doctor.speciality
                }
            except Doctor.DoesNotExist:
                # Check if user is a patient
                try:
                    from .models import Patient
                    patient = Patient.objects.get(user=user)
                    user_type = 'patient'
                    redirect_url = '/frontend/index.html'
                    profile_info = {
                        'full_name': f"{user.first_name} {user.last_name}",
                        'phone': patient.phone
                    }
                except Patient.DoesNotExist:
                    # Regular user without specific role
                    user_type = 'user'
                    redirect_url = '/frontend/index.html'
                    profile_info = {
                        'full_name': f"{user.first_name} {user.last_name}"
                    }
            
            user_data = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'user_type': user_type,
                'profile': profile_info,
                'redirect_url': redirect_url
            }
                
            return JsonResponse({
                'is_authenticated': True,
                'user': user_data
            })
        else:
            return JsonResponse({
                'is_authenticated': False,
                'user': None
            })
    except Exception as e:
        return JsonResponse({
            'is_authenticated': False,
            'user': None,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_api(request):
    """
    API endpoint for user login
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({
                'success': False,
                'message': 'Email and password are required',
                'errors': {
                    'email': ['This field is required.'] if not email else [],
                    'password': ['This field is required.'] if not password else []
                }
            }, status=400)
        
        # Try to find user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'errors': {
                    'non_field_errors': ['Invalid email or password']
                }
            }, status=400)
        
        # Authenticate user using username (Django's authenticate expects username)
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Determine user role and redirect URL
                user_type = 'user'  # default
                profile_info = {}
                redirect_url = '/frontend/index.html'  # default redirect
                
                # Check if user is a doctor
                try:
                    from .models import Doctor
                    doctor = Doctor.objects.get(user=user)
                    user_type = 'doctor'
                    redirect_url = '/frontend/pages/doctor_home.html'
                    profile_info = {
                        'full_name': f"Dr. {user.first_name} {user.last_name}",
                        'speciality': doctor.speciality
                    }
                except Doctor.DoesNotExist:
                    # Check if user is a patient
                    try:
                        from .models import Patient
                        patient = Patient.objects.get(user=user)
                        user_type = 'patient'
                        redirect_url = '/frontend/index.html'
                        profile_info = {
                            'full_name': f"{user.first_name} {user.last_name}",
                            'phone': patient.phone
                        }
                    except Patient.DoesNotExist:
                        # Regular user without specific role
                        user_type = 'user'
                        redirect_url = '/frontend/index.html'
                        profile_info = {
                            'full_name': f"{user.first_name} {user.last_name}"
                        }
                
                # Get user data
                user_data = {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_type': user_type,
                    'profile': profile_info
                }
                
                return JsonResponse({
                    'success': True,
                    'message': f'Login successful as {user_type}',
                    'user': user_data,
                    'redirect_url': redirect_url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Account is disabled',
                    'errors': {
                        'non_field_errors': ['Account is disabled']
                    }
                }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials',
                'errors': {
                    'non_field_errors': ['Invalid email or password']
                }
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Login error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register_api(request):
    """
    API endpoint for user registration
    """
    try:
        data = json.loads(request.body)
        
        # Create form with data for validation
        form = CustomUserCreationForm(data)
        
        if form.is_valid():
            # Create user
            user = form.save()
            
            # Authenticate and login the user automatically
            email = data.get('email')
            password = data.get('password1')
            
            authenticated_user = authenticate(request, username=email, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful and you are now logged in',
                    'user': {
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_authenticated': True
                    }
                })
            else:
                # User created but couldn't log in automatically
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful, please login',
                    'user': {
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_authenticated': False
                    }
                })
        else:
            # Return form errors
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
                
            return JsonResponse({
                'success': False,
                'message': 'Registration failed',
                'errors': errors
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Registration error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_api(request):
    """
    API endpoint for user logout
    """
    try:
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            return JsonResponse({
                'success': True,
                'message': f'Successfully logged out {username}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'User not logged in'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Logout error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def doctors_api(request):
    """
    API endpoint to get all doctors
    """
    try:
        doctors = Doctor.objects.select_related('user').all()
        doctors_data = []
        
        for doctor in doctors:
            doctors_data.append({
                'id': doctor.pk,
                'user': {
                    'first_name': doctor.user.first_name,
                    'last_name': doctor.user.last_name,
                    'email': doctor.user.email
                },
                'speciality': doctor.speciality,
                'phone': doctor.phone,
                'address': doctor.address,
                'license_number': doctor.license_number
            })
        
        return JsonResponse({
            'success': True,
            'data': doctors_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading doctors: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def services_api(request):
    """
    API endpoint to get all services
    """
    try:
        services = Service.objects.all()
        services_data = []
        
        for service in services:
            services_data.append({
                'id': service.pk,
                'name': service.name,
                'description': service.description
            })
        
        return JsonResponse({
            'success': True,
            'data': services_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading services: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def appointments_api(request):
    """
    API endpoint to create appointments
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)

        # Check if user is a patient
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Only patients can book appointments'
            }, status=403)

        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['date', 'time', 'doctor', 'service']
        errors = {}
        
        for field in required_fields:
            if not data.get(field):
                errors[field] = ['This field is required']
        
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Validation errors',
                'errors': errors
            }, status=400)

        # Get doctor and service objects
        try:
            doctor = Doctor.objects.get(id=data['doctor'])
        except Doctor.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Selected doctor not found'
            }, status=400)

        try:
            service = Service.objects.get(id=data['service'])
        except Service.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Selected service not found'
            }, status=400)

        # Create appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            service=service,
            date=data['date'],
            time=data['time'],
            notes=data.get('notes', ''),
            status='scheduled'
        )


        try:
            send_appointment_emails_async(appointment)
        except Exception as e:
            print(f"Email notification error: {str(e)}")
        

        return JsonResponse({
            'success': True,
            'message': 'Appointment booked successfully',
            'data': {
                'id': appointment.pk,
                'date': appointment.date,
                'time': appointment.time,
                'status': appointment.status
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating appointment: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def csrf_token_api(request):
    """
    API endpoint to get CSRF token
    """
    return JsonResponse({
        'csrfToken': get_token(request)
    })


@require_http_methods(["GET"])
def doctor_appointments_api(request):
    """
    API endpoint to get appointments for the logged-in doctor
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=401)

        # Check if user is a doctor
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Only doctors can access this endpoint'
            }, status=403)

        # Get appointments for this doctor
        appointments = Appointment.objects.filter(doctor=doctor).select_related('patient__user', 'service').order_by('-date', '-time')
        
        appointments_data = []
        for appointment in appointments:
            try:
                appointments_data.append({
                    'id': appointment.pk,
                    'patient': {
                        'first_name': appointment.patient.first_name,
                        'last_name': appointment.patient.last_name,
                        'email': appointment.patient.email,
                        'phone': appointment.patient.phone,
                        'full_name': appointment.patient.full_name
                    },
                    'service': {
                        'id': appointment.service.pk,
                        'name': appointment.service.name,
                        'description': appointment.service.description
                    },
                    'doctor': {
                        'first_name': appointment.doctor.first_name,
                        'last_name': appointment.doctor.last_name,
                        'full_name': appointment.doctor.full_name,
                        'speciality': appointment.doctor.speciality
                    },
                    'date': str(appointment.date),
                    'time': str(appointment.time),
                    'status': appointment.status,
                    'notes': appointment.notes or ''
                })
            except Exception as appt_error:
                print(f"Error processing appointment {appointment.pk}: {appt_error}")
                continue

        return JsonResponse({
            'success': True,
            'appointments': appointments_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading appointments: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def update_appointment_status_api(request, appointment_id):
    """
    Update appointment status (confirm, complete, cancel)
    """
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        
        # Get the appointment
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Appointment not found'
            }, status=404)
        
        # Check if the user is a doctor and is authorized to update this appointment
        if hasattr(request.user, 'doctor'):
            doctor = request.user.doctor
            if appointment.doctor != doctor:
                return JsonResponse({
                    'success': False,
                    'error': 'You are not authorized to update this appointment'
                }, status=403)
        elif not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Only doctors or staff can update appointment status'
            }, status=403)
        
        # Parse request data
        try:
            data = json.loads(request.body)
            new_status = data.get('status', '').lower()
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        # Validate status
        valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=400)
        
        # Update the appointment status
        old_status = appointment.status
        appointment.status = new_status
        appointment.save()
        
        # Send email notification if status changed to confirmed or cancelled
        if new_status in ['confirmed', 'cancelled'] and old_status != new_status:
            try:
                send_appointment_emails_async(appointment)
            except Exception as email_error:
                print(f"Warning: Failed to send email notification: {email_error}")
                # Don't fail the request if email fails
        
        return JsonResponse({
            'success': True,
            'message': f'Appointment status updated to {new_status}',
            'appointment': {
                'id': appointment.pk,
                'status': appointment.status,
                'previous_status': old_status
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating appointment status: {str(e)}'
        }, status=500)