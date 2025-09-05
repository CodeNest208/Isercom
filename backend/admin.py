from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from .models import Patient, Doctor, Appointment, Service


class PatientAdminForm(forms.ModelForm):
    email = forms.EmailField(help_text="Must be unique")
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput(), help_text="Enter password for the patient's login")
    
    class Meta:
        model = Patient
        fields = ['email', 'first_name', 'last_name', 'password', 'phone', 'date_of_birth', 'address']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # If editing existing patient, populate user fields
            if self.instance.user:
                self.fields['email'].initial = self.instance.user.email
                self.fields['first_name'].initial = self.instance.user.first_name
                self.fields['last_name'].initial = self.instance.user.last_name
                self.fields['password'].required = False
                self.fields['password'].help_text = "Leave blank to keep current password"
    
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
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        
        # Check if email already exists (exclude current user if editing)
        existing_user = User.objects.filter(email=email)
        if self.instance.pk and self.instance.user:
            existing_user = existing_user.exclude(pk=self.instance.user.pk)
        
        if existing_user.exists():
            raise forms.ValidationError("A user with this email already exists.")
        
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # Password is required for new patients
        if not self.instance.pk and not password:
            raise forms.ValidationError("Password is required for new patients.")
        
        # Validate password strength for new passwords
        if password:
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            
            # Check for at least one letter and one number
            if not any(c.isalpha() for c in password):
                raise forms.ValidationError("Password must contain at least one letter.")
            
            if not any(c.isdigit() for c in password):
                raise forms.ValidationError("Password must contain at least one number.")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        phone = cleaned_data.get('phone')
        
        if first_name and len(first_name.strip()) < 2:
            self.add_error('first_name', "First name must be at least 2 characters long.")
        
        if last_name and len(last_name.strip()) < 2:
            self.add_error('last_name', "Last name must be at least 2 characters long.")
        
        if phone and len(phone.strip()) < 10:
            self.add_error('phone', "Phone number must be at least 10 characters long.")
        
        return cleaned_data
    
    def save(self, commit=True):
        try:
            patient = super().save(commit=False)
            
            if not patient.user_id:
                # Creating new patient - create user first
                # Generate unique username
                username = self.generate_unique_username(
                    self.cleaned_data['first_name'], 
                    self.cleaned_data['last_name']
                )
                
                user = User.objects.create_user(
                    username=username,
                    email=self.cleaned_data['email'],
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    password=self.cleaned_data['password']
                )
                patient.user = user
                
                if commit:
                    patient.save()
                    # Now update username with patient ID for uniqueness
                    final_username = self.generate_unique_username(
                        self.cleaned_data['first_name'], 
                        self.cleaned_data['last_name'], 
                        patient.id
                    )
                    # Only update if the final username is different
                    if final_username != username:
                        user.username = final_username
                        user.save()
            else:
                # Updating existing patient - update user info
                user = patient.user
                user.email = self.cleaned_data['email']
                user.first_name = self.cleaned_data['first_name']
                user.last_name = self.cleaned_data['last_name']
                
                # Update username if name changed
                new_username = self.generate_unique_username(
                    self.cleaned_data['first_name'], 
                    self.cleaned_data['last_name'], 
                    patient.id
                )
                # Only update username if it's different and not already taken by another user
                if new_username != user.username:
                    if not User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                        user.username = new_username
                
                if self.cleaned_data['password']:
                    user.set_password(self.cleaned_data['password'])
                user.save()
            
            if commit and patient.user_id:
                patient.save()
            return patient
            
        except Exception as e:
            # Handle any unexpected errors during save
            raise forms.ValidationError(f"Error creating patient: {str(e)}")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    form = PatientAdminForm
    list_display = ('id','full_name', 'username', 'phone', 'email', 'date_of_birth', 'age')
    list_filter = ('date_of_birth',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'user__username', 'phone')
    readonly_fields = ('age',)  # Make age read-only since it's calculated from date_of_birth
    
    def username(self, obj):
        """Display the auto-generated username"""
        return obj.user.username if obj.user else 'No User'
    username.short_description = 'Username (Auto-generated)'
    fieldsets = (
        ('User Information', {
            'fields': ('email', 'first_name', 'last_name', 'password'),
            'description': 'Enter login credentials and personal information for the patient. Username will be generated automatically.'
        }),
        ('Patient Information', {
            'fields': ('phone', 'date_of_birth', 'address'),
            'description': 'Enter contact and personal information for the patient.'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            if change:
                self.message_user(request, f"Patient {obj.full_name} was updated successfully.", level='SUCCESS')
            else:
                self.message_user(request, f"Patient {obj.full_name} was created successfully. They can now log in using their email address: {obj.user.email}", level='SUCCESS')
        except Exception as e:
            self.message_user(request, f"Error saving patient: {str(e)}", level='ERROR')
            raise
    
    def delete_model(self, request, obj):
        patient_name = obj.full_name
        username = obj.user.username
        try:
            super().delete_model(request, obj)
            self.message_user(request, f"Patient {patient_name} (username: {username}) was deleted successfully.", level='SUCCESS')
        except Exception as e:
            self.message_user(request, f"Error deleting patient: {str(e)}", level='ERROR')
            raise
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'date_of_birth':
            kwargs['widget'] = forms.DateInput(attrs={'type': 'date'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class DoctorAdminForm(forms.ModelForm):
    email = forms.EmailField(help_text="Must be unique")
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput(), help_text="Enter password for the doctor's login")
    
    class Meta:
        model = Doctor
        fields = ['email', 'first_name', 'last_name', 'password', 'speciality', 'phone', 'license_number']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # If editing existing doctor, populate user fields
            if self.instance.user:
                self.fields['email'].initial = self.instance.user.email
                self.fields['first_name'].initial = self.instance.user.first_name
                self.fields['last_name'].initial = self.instance.user.last_name
                self.fields['password'].required = False
                self.fields['password'].help_text = "Leave blank to keep current password"
    
    def generate_unique_username(self, first_name, last_name, doctor_id=None):
        """Generate a unique username based on first_name, last_name, and doctor ID"""
        # Clean the names (remove spaces, convert to lowercase)
        first_clean = first_name.lower().replace(' ', '')
        last_clean = last_name.lower().replace(' ', '')
        
        if doctor_id:
            # For existing doctors, use their ID with "dr" prefix
            base_username = f"dr_{first_clean}_{last_clean}_{doctor_id}"
        else:
            # For new doctors, start with name combination with "dr" prefix
            base_username = f"dr_{first_clean}_{last_clean}"
        
        username = base_username
        counter = 1
        
        # Check if username exists and add counter if needed
        while User.objects.filter(username=username).exists():
            if doctor_id:
                username = f"{base_username}_{counter}"
            else:
                username = f"{base_username}_{counter}"
            counter += 1
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        
        # Check if email already exists (exclude current user if editing)
        existing_user = User.objects.filter(email=email)
        if self.instance.pk and self.instance.user:
            existing_user = existing_user.exclude(pk=self.instance.user.pk)
        
        if existing_user.exists():
            raise forms.ValidationError("A user with this email already exists.")
        
        return email
    
    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if license_number:
            # Check if license number already exists (exclude current doctor if editing)
            existing_doctor = Doctor.objects.filter(license_number=license_number)
            if self.instance.pk:
                existing_doctor = existing_doctor.exclude(pk=self.instance.pk)
            
            if existing_doctor.exists():
                raise forms.ValidationError("A doctor with this license number already exists.")
        
        return license_number
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # Password is required for new doctors
        if not self.instance.pk and not password:
            raise forms.ValidationError("Password is required for new doctors.")
        
        # Validate password strength for new passwords
        if password:
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            
            # Check for at least one letter and one number
            if not any(c.isalpha() for c in password):
                raise forms.ValidationError("Password must contain at least one letter.")
            
            if not any(c.isdigit() for c in password):
                raise forms.ValidationError("Password must contain at least one number.")
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation can be added here
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        speciality = cleaned_data.get('speciality')
        
        if first_name and len(first_name.strip()) < 2:
            self.add_error('first_name', "First name must be at least 2 characters long.")
        
        if last_name and len(last_name.strip()) < 2:
            self.add_error('last_name', "Last name must be at least 2 characters long.")
        
        if speciality and len(speciality.strip()) < 3:
            self.add_error('speciality', "Speciality must be at least 3 characters long.")
        
        return cleaned_data
    
    def save(self, commit=True):
        try:
            doctor = super().save(commit=False)
            
            if not doctor.user_id:
                # Creating new doctor - create user first
                # Generate unique username
                username = self.generate_unique_username(
                    self.cleaned_data['first_name'], 
                    self.cleaned_data['last_name']
                )
                
                user = User.objects.create_user(
                    username=username,
                    email=self.cleaned_data['email'],
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    password=self.cleaned_data['password']
                )
                doctor.user = user
                
                if commit:
                    doctor.save()
                    # Now update username with doctor ID for uniqueness
                    final_username = self.generate_unique_username(
                        self.cleaned_data['first_name'], 
                        self.cleaned_data['last_name'], 
                        doctor.id
                    )
                    # Only update if the final username is different
                    if final_username != username:
                        user.username = final_username
                        user.save()
            else:
                # Updating existing doctor - update user info
                user = doctor.user
                user.email = self.cleaned_data['email']
                user.first_name = self.cleaned_data['first_name']
                user.last_name = self.cleaned_data['last_name']
                
                # Update username if name changed
                new_username = self.generate_unique_username(
                    self.cleaned_data['first_name'], 
                    self.cleaned_data['last_name'], 
                    doctor.id
                )
                # Only update username if it's different and not already taken by another user
                if new_username != user.username:
                    if not User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                        user.username = new_username
                
                if self.cleaned_data['password']:
                    user.set_password(self.cleaned_data['password'])
                user.save()
            
            if commit and doctor.user_id:
                doctor.save()
            return doctor
            
        except Exception as e:
            # Handle any unexpected errors during save
            raise forms.ValidationError(f"Error creating doctor: {str(e)}")


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    form = DoctorAdminForm
    list_display = ('id', 'full_name', 'username', 'speciality', 'phone', 'license_number','email')
    list_filter = ('speciality',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'user__username', 'license_number')
    readonly_fields = ('username',)
    
    def username(self, obj):
        """Display the auto-generated username"""
        return obj.user.username if obj.user else 'No User'
    username.short_description = 'Username (Auto-generated)'
    
    fieldsets = (
        ('User Information', {
            'fields': ('email', 'first_name', 'last_name', 'password'),
            'description': 'Enter login credentials and personal information for the doctor. Username will be generated automatically with "dr_" prefix.'
        }),
        ('Doctor Information', {
            'fields': ('speciality', 'phone', 'license_number'),
            'description': 'Enter professional information for the doctor.'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            if change:
                self.message_user(request, f"Doctor {obj.full_name} was updated successfully.", level='SUCCESS')
            else:
                self.message_user(request, f"Doctor {obj.full_name} was created successfully. They can now log in using their email address: {obj.user.email}", level='SUCCESS')
        except Exception as e:
            self.message_user(request, f"Error saving doctor: {str(e)}", level='ERROR')
            raise
    
    def delete_model(self, request, obj):
        doctor_name = obj.full_name
        username = obj.user.username
        try:
            super().delete_model(request, obj)
            self.message_user(request, f"Doctor {doctor_name} (username: {username}) was deleted successfully.", level='SUCCESS')
        except Exception as e:
            self.message_user(request, f"Error deleting doctor: {str(e)}", level='ERROR')
            raise
    
    def response_add(self, request, obj, post_url_continue=None):
        # Custom response after adding a doctor
        response = super().response_add(request, obj, post_url_continue)
        return response
    
    def response_change(self, request, obj):
        # Custom response after changing a doctor
        response = super().response_change(request, obj)
        return response


class DoctorInline(admin.StackedInline):
    model = Doctor
    can_delete = False
    verbose_name_plural = 'Doctor Profile'
    fields = ('speciality', 'phone', 'license_number')
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (DoctorInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('date','time','doctor','patient','status')
    list_filter = ('status', 'date', 'doctor__speciality')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('doctor__user', 'patient__user', 'service')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name",'description')