from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class ExternalEvent(models.Model):
    PROVIDER_CHOICES = [
        ('ticketmaster', 'Ticketmaster'),
        ('seatgeek', 'SeatGeek'),
        ('eventbrite', 'Eventbrite'),
    ]
    
    external_id = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    venue_name = models.CharField(max_length=200, blank=True)
    venue_address = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    ticket_url = models.URLField(blank=True)
    price_range = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict)  # Store original API response
    fetched_at = models.DateTimeField(auto_now_add=True)
    is_imported = models.BooleanField(default=False)
    imported_event = models.ForeignKey(
        'events.Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='external_source'
    )
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['provider']),
            models.Index(fields=['start_time']),
            models.Index(fields=['is_imported']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.provider})"
    
    def clean(self):
        super().clean()
        if not self.start_time:
            raise ValidationError("Start time is required.")
        if self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
    
    @property
    def is_past(self):
        if not self.start_time:
            return False
        return self.start_time < timezone.now()
    
    @property
    def is_upcoming(self):
        if not self.start_time:
            return False
        return self.start_time > timezone.now()
