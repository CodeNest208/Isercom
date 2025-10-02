from django.apps import AppConfig
import os
import sys


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'

    def ready(self):
        """
        Called when Django starts up.
        Start the reminder scheduler automatically.
        """
        # Only start scheduler in production or when explicitly enabled
        # Avoid starting during migrations, tests, or management commands
        if (
            os.environ.get('RUN_MAIN') == 'true' or  # Django runserver reloader
            os.environ.get('ENABLE_REMINDERS') == 'true' or  # Explicit enable
            not any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'test', 'shell', 'collectstatic'])
        ):
            try:
                from .reminder_service import start_reminder_scheduler
                import logging
                
                logger = logging.getLogger(__name__)
                
                # Start the scheduler with a 1-second delay to ensure Django is fully loaded
                import threading
                def delayed_start():
                    import time
                    time.sleep(1)
                    start_reminder_scheduler(interval_minutes=5)
                    logger.info("✅ Automatic reminder scheduler started")
                
                threading.Thread(target=delayed_start, daemon=True).start()
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to start reminder scheduler: {str(e)}")
