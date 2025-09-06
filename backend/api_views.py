import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
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
        
        # Validate time restrictions (6:30 AM to 9:00 PM)
        if data.get('time'):
            try:
                from datetime import datetime
                time_obj = datetime.strptime(data['time'], '%H:%M').time()
                start_time = datetime.strptime('06:30', '%H:%M').time()
                end_time = datetime.strptime('21:00', '%H:%M').time()
                
                if time_obj < start_time or time_obj > end_time:
                    errors['time'] = ['Appointment time must be between 6:30 AM and 9:00 PM']
            except ValueError:
                errors['time'] = ['Invalid time format']
        
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
@require_http_methods(["GET"])
def my_appointments_api(request):
    """
    API endpoint to get the patient's appointments
    """
    try:
        print(f"DEBUG: my_appointments_api called by user: {request.user}")
        if not request.user.is_authenticated:
            print("DEBUG: User not authenticated")
            return JsonResponse({
                'success': False,
                'message': "Authentication required"
            }, status=401)
        
        try:
            patient = Patient.objects.get(user=request.user)
            print(f"DEBUG: Found patient: {patient}")
        except Patient.DoesNotExist:
            print("DEBUG: Patient not found")
            return JsonResponse({
                'success': False,
                'message': 'Patient profile not found. Please complete your profile first.'
            }, status=403)
        
        # Get appointments for the patient
        appointments = Appointment.objects.filter(patient=patient).select_related('doctor__user', 'service').order_by('-date', '-time')
        print(f"DEBUG: Found {appointments.count()} appointments for patient {patient.user.username}")
        appointments_data = []

        for appointment in appointments:
            try:
                appointment_dict = {
                    'id': appointment.pk,
                    'date': appointment.date.isoformat(),
                    'time': appointment.time.strftime('%H:%M'),
                    'status': appointment.status,
                    'doctor': {
                        'id': appointment.doctor.pk,
                        'name': appointment.doctor.full_name,
                        'speciality': appointment.doctor.speciality
                    },
                    'service': {
                        'id': appointment.service.pk,
                        'name': appointment.service.name,
                        'description': appointment.service.description
                    },
                    'notes': appointment.notes or '',
                    'can_cancel': appointment.status in ['scheduled', 'confirmed']
                }
                appointments_data.append(appointment_dict)
                print(f"DEBUG: Added appointment {appointment.pk}: {appointment.date} {appointment.time}")
            except Exception as appointment_error:
                print(f"DEBUG: Error processing appointment {appointment.pk}: {appointment_error}")
                continue

        response_data = {
            'success': True,
            'appointments': appointments_data
        }
        print(f"DEBUG: Returning {len(appointments_data)} appointments")
        print(f"DEBUG: Response data keys: {response_data.keys()}")
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"DEBUG: API Error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving appointments: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def cancel_appointment_api(request, appointment_id):
    """
    API endpoint to cancel a patient's appointment
    """
    try:
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': "Authentication required"
            }, status=401)
        
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Only patients can access this endpoint'
            }, status=403)
        
        try:
            appointment = Appointment.objects.get(id=appointment_id, patient=patient)
        except Appointment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Appointment not found'
            }, status=404)
        
        # Check if appointment can be cancelled
        if appointment.status not in ['scheduled', 'confirmed']:
            return JsonResponse({
                'success': False,
                'message': f'Cannot cancel appointment with status: {appointment.status}'
            }, status=400)
        
        # Cancel the appointment
        appointment.status = 'cancelled'
        appointment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Appointment cancelled successfully',
            'appointment': {
                'id': appointment.pk,
                'date': appointment.date.isoformat(),
                'time': appointment.time.strftime('%H:%M'),
                'status': appointment.status
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error cancelling appointment: {str(e)}'
        }, status=500)
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


@csrf_exempt
@require_http_methods(["POST"])
def contact_api(request):
    """
    API endpoint for contact form submissions
    Sends email to iSercom clinic
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        # Validate required fields
        if not all([name, email, subject, message]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            }, status=400)
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address.'
            }, status=400)
        
        # Prepare email content for iSercom
        email_subject = f"Website Contact Form: {subject}"
        email_message = f"""
New contact form submission from iSercom website:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

---
Reply to: {email}
Submitted on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send email to iSercom
        try:
            # Email to iSercom clinic
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],  # Use settings value
                fail_silently=False,
            )
            
            # Optional: Send confirmation email to user
            confirmation_subject = "Thank you for contacting iSercom Clinic"
            confirmation_message = f"""
Dear {name},

Thank you for contacting iSercom Medical and Fertility Centre. We have received your message regarding "{subject}" and will get back to you as soon as possible.

Our team typically responds within 24-48 hours during business days.

Best regards,
iSercom Clinic Team
            """
            
            send_mail(
                subject=confirmation_subject,
                message=confirmation_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,  # Don't fail if confirmation email fails
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your message! We will get back to you soon.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Failed to send email. Please try again later or contact us directly.'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid data format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing contact form: {str(e)}'
        }, status=500)


@require_http_methods(["GET", "PUT"])
def user_profile_api(request):
    """
    Get or update user profile information
    """
    print(f"DEBUG: user_profile_api called by user: {request.user}")
    print(f"DEBUG: user is authenticated: {request.user.is_authenticated}")
    
    if not request.user.is_authenticated:
        print("DEBUG: User not authenticated, returning 401")
        return JsonResponse({
            'success': False,
            'message': 'Authentication required.'
        }, status=401)
    
    user = request.user
    
    if request.method == 'GET':
        try:
            print(f"DEBUG: Getting profile for user: {user.username}")
            # Get user profile data
            profile_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
            print(f"DEBUG: Basic profile data: {profile_data}")
            
            # Check if user is a patient and get additional info
            try:
                patient = Patient.objects.get(user=user)
                print(f"DEBUG: Found patient record: {patient}")
                profile_data.update({
                    'phone': patient.phone,
                    'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                    'address': patient.address,
                    'user_type': 'patient'
                })
            except Patient.DoesNotExist:
                print("DEBUG: No patient record found, checking for doctor")
                # Check if user is a doctor
                try:
                    doctor = Doctor.objects.get(user=user)
                    print(f"DEBUG: Found doctor record: {doctor}")
                    profile_data.update({
                        'speciality': doctor.speciality,
                        'user_type': 'doctor'
                    })
                except Doctor.DoesNotExist:
                    print("DEBUG: No doctor record found, setting user_type to 'user'")
                    profile_data['user_type'] = 'user'
            
            print(f"DEBUG: Final profile data: {profile_data}")
            return JsonResponse(profile_data)
            
        except Exception as e:
            print(f"DEBUG: Exception in user_profile_api: {str(e)}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': f'Error retrieving profile: {str(e)}'
            }, status=500)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # Update user fields
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data:
                # Validate email
                try:
                    validate_email(data['email'])
                    user.email = data['email']
                except ValidationError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid email format.'
                    }, status=400)
            
            user.save()
            
            # Update patient-specific fields if user is a patient
            try:
                patient = Patient.objects.get(user=user)
                if 'phone' in data:
                    patient.phone = data['phone']
                if 'date_of_birth' in data and data['date_of_birth']:
                    patient.date_of_birth = data['date_of_birth']
                if 'address' in data:
                    patient.address = data['address']
                patient.save()
            except Patient.DoesNotExist:
                # If user is not a patient but tries to update patient fields, create patient record
                if any(field in data for field in ['phone', 'date_of_birth', 'address']):
                    patient = Patient.objects.create(
                        user=user,
                        phone=data.get('phone', ''),
                        date_of_birth=data.get('date_of_birth') if data.get('date_of_birth') else None,
                        address=data.get('address', '')
                    )
            
            # Return updated profile data
            # Create a mock GET request to get updated profile
            from django.http import HttpRequest
            get_request = HttpRequest()
            get_request.method = 'GET'
            get_request.user = user
            return user_profile_api(get_request)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error updating profile: {str(e)}'
            }, status=500)