# Appointment Reminder System

This system automatically sends email reminders to patients one hour before their scheduled appointments.

## Features

- ✅ Automatically sends reminder emails 1 hour before appointments
- ✅ Professional HTML email templates with clinic branding
- ✅ Prevents duplicate reminders (tracks reminder_sent status)
- ✅ Detailed logging and error handling
- ✅ Dry-run mode for testing
- ✅ Command-line management for manual testing

## Installation

1. Install the required package:
```bash
pip install django-crontab
```

2. Run migrations to add reminder tracking:
```bash
python manage.py migrate
```

## Usage

### Manual Testing

Test the reminder system with dry-run mode:
```bash
python manage.py send_appointment_reminders --dry-run
```

Send reminders manually (for testing):
```bash
python manage.py send_appointment_reminders
```

Force send reminders even if already sent:
```bash
python manage.py send_appointment_reminders --force
```

### Production Deployment

#### Option 1: Linux/Unix Systems (Recommended)

For Linux/Unix systems with cron support:

1. Add cron jobs:
```bash
python manage.py crontab add
```

2. List active cron jobs:
```bash
python manage.py crontab show
```

3. Remove cron jobs:
```bash
python manage.py crontab remove
```

#### Option 2: Windows or Alternative Schedulers

For Windows systems or when cron is not available, you can use:

1. **Windows Task Scheduler**: Set up a scheduled task to run every 5 minutes:
   ```
   Program: python
   Arguments: manage.py send_appointment_reminders
   Start in: C:\path\to\your\project
   ```

2. **Celery with Redis/RabbitMQ**: For more robust production deployments
3. **APScheduler**: Python-based scheduler (see alternative implementation below)

#### Option 3: Docker/Cloud Deployments

For containerized deployments (Heroku, Render, etc.):

1. **Heroku Scheduler**: Add a scheduled job in Heroku dashboard
2. **Render Cron Jobs**: Configure cron jobs in render.yaml
3. **Docker**: Use a sidecar container with cron

## System Architecture

### Database Changes

Added to `Appointment` model:
- `reminder_sent`: Boolean field to track if reminder was sent
- `created_at`: Timestamp for audit trail
- Database index on `(reminder_sent, date, time)` for efficient queries

### Email System

The reminder system uses the existing email infrastructure in `email_utils.py`:
- Professional HTML templates with clinic branding
- Fallback plain text versions
- Asynchronous sending to prevent blocking
- Comprehensive error handling and logging

### Scheduling Logic

The system looks for appointments:
- Between 55 and 65 minutes from current time (10-minute window)
- With status 'scheduled' or 'confirmed'
- Where `reminder_sent = False`

This ensures:
- ✅ Reminders are sent approximately 1 hour before
- ✅ No duplicate reminders
- ✅ System is fault-tolerant (can miss a few runs)

## Monitoring

### Logs

Check email logs:
```bash
tail -f email.log
```

### Database Queries

Check reminder status:
```sql
SELECT date, time, reminder_sent, patient_id, doctor_id 
FROM backend_appointment 
WHERE date >= CURDATE() 
ORDER BY date, time;
```

### Health Check

Verify the system is working:
```bash
python manage.py send_appointment_reminders --dry-run
```

## Troubleshooting

### Common Issues

1. **No reminders sent**: Check if appointments exist in the time window
2. **Email sending fails**: Verify SMTP settings in Django settings
3. **Timezone issues**: Ensure Django timezone is set correctly
4. **Permission errors**: Check file permissions for log files

### Debug Commands

```bash
# Check upcoming appointments
python manage.py shell
>>> from backend.models import Appointment
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> now = timezone.now()
>>> appointments = Appointment.objects.filter(
...     date=now.date(),
...     time__gte=(now + timedelta(minutes=55)).time(),
...     time__lte=(now + timedelta(minutes=65)).time()
... )
>>> for apt in appointments:
...     print(f"{apt.patient.full_name} - {apt.date} {apt.time} - Reminder sent: {apt.reminder_sent}")
```

## Configuration

### Email Settings

Ensure these are configured in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@isercomclinic.com'
```

### Timezone Settings

```python
TIME_ZONE = 'Your/Timezone'  # e.g., 'America/New_York'
USE_TZ = True
```

## Security Considerations

- Email credentials should be stored in environment variables
- Log files may contain patient information - secure appropriately
- Consider rate limiting for email sending
- Implement monitoring for failed email deliveries

## Future Enhancements

- SMS reminders as backup
- Multiple reminder intervals (24h, 1h, 15min)
- Patient preference management
- Reminder analytics and reporting
- Integration with calendar systems
