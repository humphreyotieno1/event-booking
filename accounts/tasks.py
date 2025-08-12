from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_activation_email_async(email, activation_link):
    try:
        logger.info(f"Sending activation email to: {email}")
        
        subject = 'Activate Your Account'
        
        try:
            html_message = render_to_string('emails/activation.html', {
                'activation_link': activation_link
            })
        except Exception as template_error:
            logger.error(f"Template rendering failed: {str(template_error)}")
            # Fallback HTML
            html_message = f"""
            <html>
                <body>
                    <h2>Activate Your Account</h2>
                    <p>Please click the link below to activate your account:</p>
                    <a href="{activation_link}">Activate Account</a>
                    <p>If the link doesn't work, copy and paste this URL:</p>
                    <p>{activation_link}</p>
                </body>
            </html>
            """
        
        plain_message = strip_tags(html_message)
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Activation email sent successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending activation email: {str(e)}")
        raise

@shared_task
def send_password_reset_email_async(email, reset_link, user_first_name=""):
    try:
        logger.info(f"Sending password reset email to: {email}")
        
        subject = 'Password Reset Request'
        
        try:
            html_message = render_to_string('emails/password_reset.html', {
                'reset_link': reset_link,
                'user_first_name': user_first_name
            })
        except Exception as template_error:
            logger.error(f"Password reset template failed: {str(template_error)}")
            # Fallback HTML
            html_message = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hello {user_first_name},</p>
                    <p>Please click the link below to reset your password:</p>
                    <a href="{reset_link}">Reset Password</a>
                    <p>If the link doesn't work, copy and paste this URL:</p>
                    <p>{reset_link}</p>
                    <p><strong>This link expires in 1 hour.</strong></p>
                </body>
            </html>
            """
        
        plain_message = strip_tags(html_message)
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        raise