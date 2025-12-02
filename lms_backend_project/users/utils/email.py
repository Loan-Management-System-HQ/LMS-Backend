from django.conf import settings
from django.core.mail import send_mail


def send_password_reset_email(user, reset_url):
    """
    Send password reset email to user
    """
    subject = "Reset Your Password - Loan Management System"

    # Create plain text version
    plain_message = f"""
    Password Reset Request

    Hello {user.name},

    You requested to reset your password for the Loan Management System.

    Click this link to reset your password:
    {reset_url}

    This link will expire in 24 hours.

    If you didn't request this password reset, please ignore this email.

    Best regards,
    Loan Management System Team
    """

    # Send email
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False


def send_simple_email(subject, message, recipient_list):
    """
    Simple email sender for other notifications
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False
