from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from datetime import timedelta
import logging

from .models import User
from .tasks import send_activation_email_async

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def send_activation_email_signal(sender, instance, created, **kwargs):
    if created and not instance.email_verified:
        # Generate token that expires in 24 hours
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)
        expiration = (timezone.now() + timedelta(hours=24)).timestamp()
        
        confirm_url = (
            f"{settings.FRONTEND_URL}/api/accounts/verify-email/"
            f"?uid={uid}&token={token}&expires={expiration}"
        )

        try:
            send_activation_email_async.delay(instance.email, confirm_url)
        except Exception as e:
            logger.error(f"Failed to send activation email: {str(e)}")