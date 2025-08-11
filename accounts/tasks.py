from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@shared_task
def send_activation_email_async(email, activation_link):
    subject = 'Activate Your Account'
    html_message = render_to_string('emails/activation.html', {
        'activation_link': activation_link
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

@shared_task
def send_password_reset_email_async(email, reset_link, user_first_name=""):
    subject = 'Password Reset Request'
    html_message = render_to_string('emails/password_reset.html', {
        'reset_link': reset_link,
        'user_first_name': user_first_name
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )