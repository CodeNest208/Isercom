from django.db import models
from django.contrib.auth.models import User

# Add User properties for role checking
@property
def is_patient(self):
    return hasattr(self, 'patient')

@property
def is_doctor(self):
    return hasattr(self, 'doctor')

@property
def user_type(self):
    if hasattr(self, 'doctor'):
        return 'doctor'
    elif hasattr(self, 'patient'):
        return 'patient'
    return 'user'

@property
def profile_name(self):
    if hasattr(self, 'doctor'):
        return f"Dr. {self.first_name} {self.last_name}"
    elif hasattr(self, 'patient'):
        return f"{self.first_name} {self.last_name}"
    return f"{self.first_name} {self.last_name}"

# Add these properties to the User model
User.add_to_class('is_patient', is_patient)
User.add_to_class('is_doctor', is_doctor)
User.add_to_class('user_type', user_type)
User.add_to_class('profile_name', profile_name)

# Create your models here.
class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=30, db_index=True)  # Add index for search
    date_of_birth = models.DateField(null=True, blank=True, db_index=True)  # Add index for age queries
    address = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),  # Index for user relationship
            models.Index(fields=['phone']),  # Index for phone searches
        ]

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    def __str__(self) -> str:
        return self.full_name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    speciality = models.CharField(max_length=255, db_index=True)  # Add index for specialty searches
    phone = models.CharField(max_length=30)
    address = models.TextField(null=True, blank=True)
    license_number = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),  # Index for user relationship
            models.Index(fields=['speciality']),  # Index for specialty searches
            models.Index(fields=['license_number']),  # Index for license searches
        ]

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    @property
    def full_name(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    def __str__(self) -> str:
        return self.full_name

class Service(models.Model):
    
    description = models.CharField(max_length=600)
    name = models.CharField(max_length=255)

    def __str__(self)-> str:
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    date = models.DateField(db_index=True)  # Add index for date queries
    time = models.TimeField()
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='scheduled', db_index=True)  # Add index for status filtering
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE) 
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or specific concerns")
    reminder_sent = models.BooleanField(default=False, help_text="Whether reminder email has been sent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['patient', 'date']),  # For patient appointment queries
            models.Index(fields=['doctor', 'date']),   # For doctor appointment queries
            models.Index(fields=['date', 'status']),   # For status-based queries
            models.Index(fields=['doctor', 'status']), # For doctor status filtering
            models.Index(fields=['patient', 'status']), # For patient status filtering
            models.Index(fields=['reminder_sent', 'date', 'time']), # For reminder queries
        ]

    @property
    def appointment_datetime(self):
        """Return appointment date and time as datetime object"""
        from datetime import datetime, timezone
        return datetime.combine(self.date, self.time)

    def __str__(self) -> str:
        return f"{self.patient.full_name} - {self.doctor.full_name} - {self.date} {self.time}"

