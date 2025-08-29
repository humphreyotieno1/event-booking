from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class EventCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Event Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class EventTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    max_attendees = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)]
    )
    external_event_id = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    tags = models.ManyToManyField(EventTag, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['title']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_past(self):
        return self.end_time < timezone.now()
    
    @property
    def is_full(self):
        if not self.max_attendees:
            return False
        return self.rsvps.filter(status='going').count() >= self.max_attendees
    
    @property
    def current_attendee_count(self):
        return self.rsvps.filter(status='going').count()
    
    @property
    def available_spots(self):
        if not self.max_attendees:
            return None
        return max(0, self.max_attendees - self.current_attendee_count)
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)

class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.rating}/5)"
    
    def clean(self):
        # Only allow reviews for past events
        if not self.event.is_past:
            raise ValidationError("Can only review past events.")
        
        # User must have attended the event
        if not hasattr(self.user, 'rsvps') or not self.user.rsvps.filter(event=self.event, status='going').exists():
            raise ValidationError("Can only review events you attended.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
