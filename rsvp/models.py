from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class RSVP(models.Model):
    RSVP_STATUS_CHOICES = [
        ('going', 'Going'),
        ('interested', 'Interested'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rsvps'
    )
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='rsvps'
    )
    status = models.CharField(
        max_length=20,
        choices=RSVP_STATUS_CHOICES,
        default='going'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.status})"
    
    def clean(self):
        # Check if event is full when RSVPing as 'going'
        if self.status == 'going' and self.event.is_full:
            raise ValidationError("This event is already at full capacity.")
        
        # Check if event is in the past
        if self.event.is_past:
            raise ValidationError("Cannot RSVP to past events.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
