from django.contrib import admin
from .models import Event, EventCategory, EventTag, Review

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    ordering = ['name']

@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'created_by', 'location', 'start_time', 
        'end_time', 'max_attendees', 'current_attendee_count',
        'is_full', 'is_past', 'category'
    ]
    list_filter = [
        'category', 'is_recurring', 'created_at', 'start_time',
        'created_by__is_organizer'
    ]
    search_fields = ['title', 'description', 'location', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'current_attendee_count', 'is_full', 'is_past']
    filter_horizontal = ['tags']
    date_hierarchy = 'start_time'
    
    def current_attendee_count(self, obj):
        return obj.current_attendee_count
    current_attendee_count.short_description = 'Attendees'
    
    def is_full(self, obj):
        return obj.is_full
    is_full.boolean = True
    is_full.short_description = 'Full'
    
    def is_past(self, obj):
        return obj.is_past
    is_past.boolean = True
    is_past.short_description = 'Past'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'event__title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
