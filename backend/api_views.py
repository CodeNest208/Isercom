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

        return JsonResponse({
            'success': True,
            'message': 'Appointment booked successfully',
            'data': {
                'id': appointment.pk,
                'date': appointment.date.strftime('%Y-%m-%d'),
                'time': appointment.time.strftime('%H:%M'),
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