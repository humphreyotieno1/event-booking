from django.contrib import admin
from .models import ExternalEvent

@admin.register(ExternalEvent)
class ExternalEventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'provider', 'location', 'start_time', 
        'is_imported', 'fetched_at', 'is_past'
    ]
    list_filter = [
        'provider', 'is_imported', 'fetched_at', 'start_time'
    ]
    search_fields = ['title', 'description', 'location', 'external_id']
    readonly_fields = ['fetched_at', 'is_past', 'is_upcoming']
    date_hierarchy = 'start_time'
    
    def is_past(self, obj):
        return obj.is_past
    is_past.boolean = True
    is_past.short_description = 'Past'
    
    def is_upcoming(self, obj):
        return obj.is_upcoming
    is_upcoming.boolean = True
    is_upcoming.short_description = 'Upcoming'
