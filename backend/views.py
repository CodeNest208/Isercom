from django.shortcuts import get_object_or_404
from backend.models import Appointment
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from backend.forms import EmailAuthenticationForm

# Essential views for API-based frontend

class CustomLoginView(LoginView):
    """
    Custom login view that uses email instead of username
    """
    form_class = EmailAuthenticationForm
    template_name = 'frontend/pages/login.html'  # Points to frontend file
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Add success message when user logs in successfully"""
        user = form.get_user()
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


def logout_view(request):
    """Custom logout view that works with both GET and POST requests"""
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        logout(request)
        messages.success(
            request, 
            f'👋 Thank you for visiting iSercom Clinic, {username}! You have been safely signed out.'
        )
    from django.shortcuts import redirect
    return redirect('/')


@login_required
def update_appointment_status(request, appointment_id):
    """View for doctors to update appointment status - API endpoint"""
    if not hasattr(request.user, 'doctor'):
        messages.error(
            request, 
            '🚫 Unauthorized access. Only doctors can update appointment statuses.'
        )
        from django.http import JsonResponse
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor__user', 'patient__user'), 
        id=appointment_id, 
        doctor=request.user.doctor
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled']
        
        if new_status in valid_statuses:
            appointment.status = new_status
            appointment.save()
            
            status_messages = {
                'confirmed': f'✅ Appointment with {appointment.patient.user.get_full_name()} has been confirmed.',
                'completed': f'✅ Appointment with {appointment.patient.user.get_full_name()} has been marked as completed.',
                'cancelled': f'❌ Appointment with {appointment.patient.user.get_full_name()} has been cancelled.',
                'scheduled': f'📅 Appointment with {appointment.patient.user.get_full_name()} has been rescheduled.'
            }
            
            messages.success(
                request, 
                status_messages.get(new_status, f'✅ Appointment status updated to {new_status.title()}.')
            )
            
            from django.http import JsonResponse
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
        else:
            from django.http import JsonResponse
            return JsonResponse({'error': 'Invalid status'}, status=400)
    
    from django.http import JsonResponse
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def serve_frontend_file(request, file_path='index.html'):
    """Serve any file from the frontend directory"""
    from django.http import FileResponse, Http404
    from django.conf import settings
    import os
    import mimetypes
    
    # Construct the full path to the requested file
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', file_path)
    
    # Security check - ensure the path is within the frontend directory
    frontend_dir = os.path.join(settings.BASE_DIR, 'frontend')
    if not os.path.abspath(frontend_path).startswith(os.path.abspath(frontend_dir)):
        raise Http404("File not found")
    
    if os.path.exists(frontend_path) and os.path.isfile(frontend_path):
        # Determine the content type
        content_type, _ = mimetypes.guess_type(frontend_path)
        if not content_type:
            if file_path.endswith('.html'):
                content_type = 'text/html'
            elif file_path.endswith('.css'):
                content_type = 'text/css'
            elif file_path.endswith('.js'):
                content_type = 'application/javascript'
            else:
                content_type = 'application/octet-stream'
        
        return FileResponse(open(frontend_path, 'rb'), content_type=content_type)
    else:
        raise Http404("File not found")