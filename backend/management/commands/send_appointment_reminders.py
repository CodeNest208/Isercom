from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from backend.models import Appointment
from backend.email_utils import send_appointment_reminder_to_patient
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send appointment reminder emails to patients one hour before their appointment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which reminders would be sent without actually sending them',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Send reminders even if they were already sent (for testing)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Starting appointment reminder check...')
        )
        
        # Get current time
        now = timezone.now()
        
        # Calculate the time window (1 hour from now, with 5-minute buffer)
        reminder_time_start = now + timedelta(minutes=55)  # 55 minutes from now
        reminder_time_end = now + timedelta(minutes=65)    # 65 minutes from now
        
        self.stdout.write(
            f"Looking for appointments between {reminder_time_start.strftime('%Y-%m-%d %H:%M')} "
            f"and {reminder_time_end.strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Find appointments that need reminders
        appointments_query = Appointment.objects.filter(
            date=reminder_time_start.date(),
            time__gte=reminder_time_start.time(),
            time__lte=reminder_time_end.time(),
            status__in=['scheduled', 'confirmed']
        )
        
        # If not forcing, exclude appointments that already have reminders sent
        if not force:
            appointments_query = appointments_query.filter(reminder_sent=False)
        
        appointments = appointments_query.select_related('patient__user', 'doctor__user', 'service')
        
        if not appointments.exists():
            self.stdout.write(
                self.style.WARNING('No appointments found that need reminders.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {appointments.count()} appointment(s) that need reminders:')
        )
        
        sent_count = 0
        failed_count = 0
        
        for appointment in appointments:
            appointment_datetime = datetime.combine(appointment.date, appointment.time)
            patient_name = appointment.patient.full_name
            patient_email = appointment.patient.email
            doctor_name = appointment.doctor.full_name
            
            self.stdout.write(
                f"  - {patient_name} ({patient_email}) with {doctor_name} "
                f"on {appointment_datetime.strftime('%Y-%m-%d %H:%M')}"
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('    [DRY RUN] Would send reminder email')
                )
                sent_count += 1
            else:
                try:
                    # Send the reminder email
                    success = send_appointment_reminder_to_patient(
                        appointment, 
                        async_send=False  # Send synchronously for management command
                    )
                    
                    if success:
                        # Mark reminder as sent
                        appointment.reminder_sent = True
                        appointment.save(update_fields=['reminder_sent'])
                        
                        self.stdout.write(
                            self.style.SUCCESS('    ✓ Reminder email sent successfully')
                        )
                        sent_count += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR('    ✗ Failed to send reminder email')
                        )
                        failed_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'    ✗ Error sending reminder: {str(e)}')
                    )
                    failed_count += 1
                    logger.error(f"Error sending reminder for appointment {appointment.pk}: {str(e)}")
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(f'\nReminder check completed:')
        )
        self.stdout.write(f'  - Reminders sent: {sent_count}')
        if failed_count > 0:
            self.stdout.write(
                self.style.ERROR(f'  - Failed to send: {failed_count}')
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a dry run. No emails were actually sent.')
            )
