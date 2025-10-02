"""
Automatic Reminder Scheduler integrated with Django
This can be imported and started from within Django apps or views
"""
import threading
import time
import logging
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self, interval_minutes=5):
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the reminder scheduler"""
        if self.running:
            logger.warning("Reminder scheduler is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info(f"Reminder scheduler started (checking every {self.interval_minutes} minutes)")
        
    def stop(self):
        """Stop the reminder scheduler"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        logger.info("Reminder scheduler stopped")
        
    def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        while self.running:
            try:
                logger.info("Running appointment reminder check...")
                # Call the management command
                call_command('send_appointment_reminders', verbosity=0)
                logger.info("Appointment reminder check completed")
                
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {str(e)}")
                
            # Wait for the next check
            for _ in range(self.interval_seconds):
                if not self.running:
                    break
                time.sleep(1)

# Global scheduler instance
_scheduler = None

def start_reminder_scheduler(interval_minutes=5):
    """Start the global reminder scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ReminderScheduler(interval_minutes)
    _scheduler.start()
    return _scheduler

def stop_reminder_scheduler():
    """Stop the global reminder scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()

def get_scheduler():
    """Get the current scheduler instance"""
    return _scheduler

def is_scheduler_running():
    """Check if the scheduler is currently running"""
    return _scheduler and _scheduler.running
