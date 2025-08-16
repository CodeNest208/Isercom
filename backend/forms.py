from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from backend.models import Appointment, Patient, Doctor, Service


class EmailAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that uses email instead of username for login.
    """
    username = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password'
        })
    )
    
    error_messages = {
        'invalid_login': (
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': "This account is inactive.",
    }

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your first name'
        }),
        label='First Name'
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your last name'
        }),
        label='Last Name'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address'
        }),
        label='Email Address'
    )
    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your phone number'
        }),
        label='Phone Number'
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'Select your date of birth'
        }),
        label='Date of Birth'
    )
    
    terms_agreement = forms.BooleanField(
        required=True,
        label='Terms and Conditions Agreement',
        error_messages={
            'required': 'You must agree to the terms and conditions to create an account.'
        },
        widget=forms.CheckboxInput(attrs={
            'id': 'terms_agreement'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since it will be auto-generated
        if 'username' in self.fields:
            del self.fields['username']
        
        # Add styling to remaining fields
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm your password'
        })

    def generate_unique_username(self, first_name, last_name, patient_id=None):
        """Generate a unique username based on first_name, last_name, and patient ID"""
        # Clean the names (remove spaces, convert to lowercase)
        first_clean = first_name.lower().replace(' ', '')
        last_clean = last_name.lower().replace(' ', '')
        
        if patient_id:
            # For existing patients, use their ID
            base_username = f"{first_clean}_{last_clean}_{patient_id}"
        else:
            # For new patients, start with name combination
            base_username = f"{first_clean}_{last_clean}"
        
        username = base_username
        counter = 1
        
        # Check if username exists and add counter if needed
        while User.objects.filter(username=username).exists():
            if patient_id:
                username = f"{base_username}_{counter}"
            else:
                username = f"{base_username}_{counter}"
            counter += 1
        
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        # Generate unique username before saving
        username = self.generate_unique_username(
            self.cleaned_data['first_name'], 
            self.cleaned_data['last_name']
        )
        
        # Create user with generated username
        user = User.objects.create_user(
            username=username,
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password1']
        )
        
        if commit:
            try:
                user.save()
                # Create patient profile with phone and date_of_birth
                patient = Patient.objects.create(
                    user=user,
                    phone=self.cleaned_data['phone'],
                    date_of_birth=self.cleaned_data.get('date_of_birth')
                )
                
                # Update username with patient ID for uniqueness
                if patient.pk:
                    final_username = self.generate_unique_username(
                        self.cleaned_data['first_name'], 
                        self.cleaned_data['last_name'], 
                        patient.pk
                    )
                    # Only update if the final username is different
                    if final_username != username:
                        user.username = final_username
                        user.save()
            except Exception as e:
                # If patient creation fails, clean up the user to avoid orphaned records
                if user.pk:
                    user.delete()
                raise e  # Re-raise the exception so it can be handled by the view
                
        return user

class AppointmentForm(forms.ModelForm):
    # Override doctor field to optimize queries
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.select_related('user').all(),
        widget=forms.Select(),
        label='Select Doctor'
    )
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'service', 'date', 'time', 'notes']  # Removed 'message' field, keeping only 'notes'
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'step': '3600'  # 1-hour intervals
            }),
            'service': forms.Select(),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Enter your name, notes, or any specific concerns for this appointment'
            })
        }
        labels = {
            'service': 'Select Service',
            'date': 'Appointment Date',
            'time': 'Appointment Time',
            'notes': 'Notes/Message'
        }