import os

import django
from django.core.mail import send_mail

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms_backend_project.settings")
django.setup()

send_mail(
    "Test Email from Loan System",
    "This is a test email to verify configuration.",
    os.environ.get("EMAIL_HOST_USER"),
    ["bhavik.knight@gmail.com"],  # Change this to your email
    fail_silently=False,
)
print("Email sent!")
