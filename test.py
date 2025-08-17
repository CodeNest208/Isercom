import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isercom_website.settings')

import django
django.setup()


from django.core.mail import send_mail
send_mail('Test', 'Hello', 'felixasante2005@gmail.com', ['felixasante2005@gmail.com'])