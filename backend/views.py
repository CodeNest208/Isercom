from django.shortcuts import render, redirect, get_object_or_404
from backend.models import Patient, Appointment, Doctor, Service
from backend.forms import AppointmentForm, CustomUserCreationForm, EmailAuthenticationForm
from backend.email_utils import send_appointment_notification_to_doctor, send_appointment_confirmation_to_patient, send_appointment_emails_async
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from datetime import date, timedelta

# Create your views here.

class CustomLoginView(LoginView):
    """
    Custom login view that uses email instead of username
    """
    form_class = EmailAuthenticationForm
    template_name = 'login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Add success message when user logs in successfully"""
        user = form.get_user()
        # Create a personalized welcome message
        first_name = user.first_name if user.first_name else user.username
        messages.success(
            self.request, 
            f'🎉 Welcome back, {first_name}! You have successfully signed in to your account.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Add error message when login fails"""
        messages.error(
            self.request,
            '❌ Invalid email or password. Please check your credentials and try again.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return '/'  # Redirect to home after successful login


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Save the form to create the user and patient profile
                user = form.save()
                
                # Get the email and password to authenticate (since we use email-based auth)
                email = form.cleaned_data.get('email')
                password = form.cleaned_data.get('password1')
                
                # Authenticate and login the user using email
                authenticated_user = authenticate(request, username=email, password=password)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    messages.success(
                        request, 
                        f'🎉 Welcome to iSercom Clinic, {user.first_name}! Your account has been created successfully and you are now signed in. You can now book appointments and access all our services.'
                    )
                    return redirect('home')  # User is now logged in
                else:
                    messages.warning(
                        request, 
                        f'✅ Your account has been created successfully, {user.first_name}! However, there was an issue signing you in automatically. Please sign in using your email address and password.'
                    )
                    return redirect('login')
            except Exception as e:
                # If there's any error during user/patient creation, show error message
                messages.error(
                    request, 
                    '❌ We encountered an error while creating your account. Please try again or contact our support team if the problem continues.'
                )
                # Re-initialize the form to show it again
                form = CustomUserCreationForm()
        else:
            # Form validation failed
            messages.error(
                request, 
                '⚠️ Please review and correct the highlighted errors below before submitting.'
            )
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    """Custom logout view that works with both GET and POST requests"""
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        logout(request)
        messages.success(
            request, 
            f'👋 Thank you for visiting iSercom Clinic, {username}! You have been safely signed out. We look forward to seeing you again soon.'
        )
    return redirect('home')


@login_required
def create_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                # Get patient record for current user using select_related
                patient = Patient.objects.select_related('user').get(user=request.user)
                
                appointment = form.save(commit=False)
                appointment.patient = patient
                appointment.status = 'scheduled'
                appointment.save()
                
                # Send email notifications asynchronously for faster response
                try:
                    # Start async email sending in background
                    send_appointment_emails_async(appointment)
                    
                    # Immediate success message - emails will be sent in background
                    messages.success(
                        request, 
                        f'🎉 Excellent! Your appointment has been successfully booked for {appointment.date.strftime("%B %d, %Y")} at {appointment.time.strftime("%I:%M %p")} with {appointment.doctor.user.get_full_name()}. Confirmation emails are being sent to you and your doctor.'
                    )
                        
                except Exception as e:
                    # Even if email fails, appointment was still created successfully
                    messages.success(
                        request, 
                        f'✅ Your appointment has been successfully booked for {appointment.date.strftime("%B %d, %Y")} at {appointment.time.strftime("%I:%M %p")} with {appointment.doctor.user.get_full_name()}!'
                    )
                    messages.info(
                        request, 
                        '📧 Note: Email confirmations are being processed and will be sent shortly. Your appointment is confirmed regardless.'
                    )
                
                return redirect('appointment_success')
                
            except Patient.DoesNotExist:
                messages.error(
                    request, 
                    '⚠️ We need to complete your patient profile before you can book appointments. Please update your information below.'
                )
                return redirect('register')
        else:
            messages.error(
                request, 
                '📝 Please review the form and correct any errors highlighted below.'
            )
    else:
        form = AppointmentForm()

    # Get doctors and services for the template
    doctors = Doctor.objects.select_related('user').all()
    services = Service.objects.all()
    
    context = {
        'form': form,
        'doctors': doctors,
        'services': services,
    }
    return render(request, 'appointment_form.html', context)


@login_required
def my_appointments(request):
    """View to show all appointments for the current user"""
    try:
        patient = Patient.objects.select_related('user').get(user=request.user)
        appointments = Appointment.objects.select_related('doctor__user', 'patient__user', 'service').filter(patient=patient).order_by('-date', '-time')
        
        if not appointments.exists():
            messages.info(
                request,
                f'📅 Hi {request.user.first_name}! You don\'t have any appointments scheduled yet. Would you like to book your first appointment with us?'
            )
        
    except Patient.DoesNotExist:
        appointments = []
        messages.warning(
            request, 
            f'⚠️ Hello {request.user.username}! We couldn\'t find your patient profile in our system. Please contact our support team or complete your registration to view your appointments.'
        )
    
    # Also check if user might be a doctor
    if hasattr(request.user, 'doctor'):
        messages.info(
            request, 
            '👨‍⚕️ You are currently viewing the patient appointments page. As a doctor, you may want to visit your doctor dashboard instead.'
        )
    
    context = {
        'appointments': appointments,
        'user': request.user
    }
    return render(request, 'my_appointments.html', context)

@login_required
def appointment_success(request):
    messages.success(
        request,
        '🎊 Congratulations! Your appointment booking has been completed successfully. You should receive a confirmation email shortly with all the details.'
    )
    return render(request, 'appointment_successful.html')


@login_required
def doctor_dashboard(request):
    """Dashboard view for doctors"""
    if not hasattr(request.user, 'doctor'):
        messages.error(
            request, 
            '🚫 Access restricted. This area is exclusively for registered doctors. If you believe this is an error, please contact our administrator.'
        )
        return redirect('home')
    
    doctor = request.user.doctor
    
    # Get today's appointments
    today_appointments = Appointment.objects.select_related('patient__user', 'service').filter(
        doctor=doctor, 
        date=date.today()
    ).order_by('time')
    
    # Get upcoming appointments (next 30 days)
    upcoming_appointments = Appointment.objects.select_related('patient__user', 'service').filter(
        doctor=doctor,
        date__gte=date.today(),
        date__lte=date.today() + timedelta(days=30)
    ).order_by('date', 'time')
    
    # Get all appointments for this doctor
    all_appointments = Appointment.objects.select_related('patient__user', 'service').filter(doctor=doctor).order_by('-date', '-time')
    
    # Get appointment statistics using aggregate queries
    from django.db.models import Count, Q
    stats = Appointment.objects.filter(doctor=doctor).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='scheduled')),
        confirmed=Count('id', filter=Q(status='confirmed')),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled'))
    )
    
    # Get recent appointments (last 10)
    recent_appointments = Appointment.objects.select_related('patient__user', 'service').filter(doctor=doctor).order_by('-date', '-time')[:10]
    
    # Welcome message for doctor
    if today_appointments.exists():
        messages.info(
            request,
            f'👋 Good day, Dr. {doctor.user.get_full_name()}! You have {today_appointments.count()} appointment(s) scheduled for today. Have a productive day!'
        )
    else:
        messages.info(
            request,
            f'👋 Good day, Dr. {doctor.user.get_full_name()}! You have no appointments scheduled for today. Enjoy your day!'
        )
    
    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'all_appointments': all_appointments,
        'recent_appointments': recent_appointments,
        'total_appointments': stats['total'],
        'pending_appointments': stats['pending'],
        'confirmed_appointments': stats['confirmed'],
        'completed_appointments': stats['completed'],
        'cancelled_appointments': stats['cancelled'],
    }
    
    return render(request, 'doctor_dashboard.html', context)


@login_required
def patient_dashboard(request):
    """Dashboard view for patients"""
    if not hasattr(request.user, 'patient'):
        messages.error(
            request, 
            '🚫 Access restricted. This area is for registered patients only. If you need to register as a patient, please complete the registration process.'
        )
        return redirect('home')
    
    patient = request.user.patient
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.select_related('doctor__user', 'service').filter(
        patient=patient,
        date__gte=date.today()
    ).order_by('date', 'time')
    
    # Get appointment history
    past_appointments = Appointment.objects.select_related('doctor__user', 'service').filter(
        patient=patient,
        date__lt=date.today()
    ).order_by('-date', '-time')[:5]  # Last 5 appointments
    
    # Welcome message for patient
    if upcoming_appointments.exists():
        next_appointment = upcoming_appointments.first()
        if next_appointment:
            messages.info(
                request,
                f'👋 Welcome back, {patient.user.first_name}! Your next appointment is on {next_appointment.date.strftime("%B %d, %Y")} at {next_appointment.time.strftime("%I:%M %p")} with {next_appointment.doctor.user.get_full_name()}.'
            )
        else:
            messages.info(
                request,
                f'👋 Hello {patient.user.first_name}! You don\'t have any upcoming appointments. Would you like to schedule a visit with one of our specialists?'
            )
    else:
        messages.info(
            request,
            f'👋 Hello {patient.user.first_name}! You don\'t have any upcoming appointments. Would you like to schedule a visit with one of our specialists?'
        )
    
    context = {
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
    }
    
    return render(request, 'patient_dashboard.html', context)


@login_required
def doctor_appointments(request):
    """View for doctors to manage all their appointments"""
    if not hasattr(request.user, 'doctor'):
        messages.error(
            request, 
            '🚫 Access denied. This appointments management area is exclusively for doctors. Please ensure you are logged in with a doctor account.'
        )
        return redirect('home')
    
    doctor = request.user.doctor
    
    # Filter appointments by status if requested
    status_filter = request.GET.get('status', 'all')
    
    if status_filter == 'all':
        appointments = Appointment.objects.select_related('patient__user', 'service').filter(doctor=doctor)
    else:
        appointments = Appointment.objects.select_related('patient__user', 'service').filter(doctor=doctor, status=status_filter)
    
    # Order by date and time
    appointments = appointments.order_by('-date', '-time')
    
    # Get statistics for filtering using aggregate
    from django.db.models import Count, Q
    stats_data = Appointment.objects.filter(doctor=doctor).aggregate(
        all=Count('id'),
        scheduled=Count('id', filter=Q(status='scheduled')),
        confirmed=Count('id', filter=Q(status='confirmed')),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled'))
    )
    
    # Status filter message
    if status_filter != 'all':
        filter_count = appointments.count()
        messages.info(
            request,
            f'📊 Showing {filter_count} appointment(s) with status: {status_filter.title()}. Click "All" to view all appointments.'
        )
    
    context = {
        'doctor': doctor,
        'appointments': appointments,
        'current_filter': status_filter,
        'stats': stats_data,
    }
    
    return render(request, 'doctor_appointments.html', context)


@login_required
def update_appointment_status(request, appointment_id):
    """View for doctors to update appointment status"""
    if not hasattr(request.user, 'doctor'):
        messages.error(
            request, 
            '🚫 Unauthorized access. Only doctors can update appointment statuses.'
        )
        return redirect('home')
    
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor__user', 'patient__user'), 
        id=appointment_id, 
        doctor=request.user.doctor
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled']
        
        if new_status in valid_statuses:
            old_status = appointment.status
            appointment.status = new_status
            appointment.save()
            
            # Create status-specific messages
            status_messages = {
                'confirmed': f'✅ Appointment with {appointment.patient.user.get_full_name()} has been confirmed for {appointment.date.strftime("%B %d, %Y")} at {appointment.time.strftime("%I:%M %p")}.',
                'completed': f'✅ Appointment with {appointment.patient.user.get_full_name()} has been marked as completed.',
                'cancelled': f'❌ Appointment with {appointment.patient.user.get_full_name()} scheduled for {appointment.date.strftime("%B %d, %Y")} has been cancelled.',
                'scheduled': f'📅 Appointment with {appointment.patient.user.get_full_name()} has been rescheduled for {appointment.date.strftime("%B %d, %Y")} at {appointment.time.strftime("%I:%M %p")}.'
            }
            
            messages.success(
                request, 
                status_messages.get(new_status, f'✅ Appointment status updated to {new_status.title()}.')
            )
        else:
            messages.error(
                request, 
                '❌ Invalid status selected. Please choose a valid appointment status.'
            )
    
    return redirect('doctor_appointments')



def home(request):
    if request.user.is_authenticated:
        # Use a single query to check user relationships
        try:
            # Check if user is a doctor using hasattr (no additional DB query)
            if hasattr(request.user, 'doctor'):
                doctor = request.user.doctor
                return render(request, 'doctor_home.html', {
                    'doctor': doctor,
                    'user': request.user
                })
            # Check if user is a patient using hasattr (no additional DB query)
            elif hasattr(request.user, 'patient'):
                patient = request.user.patient
                return render(request, 'index.html', {
                    'patient': patient,
                    'user': request.user
                })
            else:
                # User has no profile, redirect to create patient profile or show generic home
                messages.info(
                    request, 
                    '👋 Welcome to iSercom Clinic! To access all our features and book appointments, please complete your profile by registering as a patient.'
                )
                return render(request, 'index.html')
        except AttributeError:
            # Handle potential attribute errors gracefully
            messages.info(
                request, 
                '👋 Welcome back! To ensure you have access to all features, please verify that your profile is complete.'
            )
            return render(request, 'index.html')
    else:
        # Not authenticated, show general home page
        return render(request, 'index.html')

# Static Frontend Pages (No backend data required)
def about_us(request):
    """About Us page"""
    return render(request, 'static/about_us.html')

def services(request):
    """Services page"""
    return render(request, 'static/services.html')

def contact(request):
    """Contact page"""
    return render(request, 'static/contact.html')

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'static/privacy_policy.html')

def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'static/terms_of_service.html')

def faq(request):
    """Frequently Asked Questions page"""
    return render(request, 'static/faq.html')

def gynaecology(request):
    return render(request, 'static/gynaecology.html')

def fertility(request):
    return render(request,'static/fertility.html')

def antenatal(request):
    return render(request,'static/Antenatal.html')

def consultation(request):
    return render(request,'static/consultation.html')