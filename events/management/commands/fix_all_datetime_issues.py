from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event
from external_events.models import ExternalEvent
from datetime import timedelta

class Command(BaseCommand):
    help = 'Fix all datetime-related issues across all apps'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Starting comprehensive datetime fix...')
        
        # Fix Events
        self.fix_events()
        
        # Fix External Events
        self.fix_external_events()
        
        self.stdout.write(
            self.style.SUCCESS('✅ All datetime issues have been fixed!')
        )
    
    def fix_events(self):
        """Fix events with None end_time"""
        self.stdout.write('📅 Fixing Events...')
        
        events_without_end_time = Event.objects.filter(end_time__isnull=True)
        
        if not events_without_end_time.exists():
            self.stdout.write('  ✅ No events found with None end_time')
            return
        
        self.stdout.write(f'  🔧 Found {events_without_end_time.count()} events with None end_time')
        
        fixed_count = 0
        for event in events_without_end_time:
            if event.start_time:
                # Set end_time to 2 hours after start_time
                event.end_time = event.start_time + timedelta(hours=2)
                event.save()
                fixed_count += 1
                self.stdout.write(f'    ✅ Fixed event "{event.title}"')
            else:
                # If both start_time and end_time are None, set both to now
                now = timezone.now()
                event.start_time = now
                event.end_time = now + timedelta(hours=2)
                event.save()
                fixed_count += 1
                self.stdout.write(f'    ✅ Fixed event "{event.title}" (both times)')
        
        self.stdout.write(f'  ✅ Fixed {fixed_count} events')
    
    def fix_external_events(self):
        """Fix external events with None start_time"""
        self.stdout.write('🌐 Fixing External Events...')
        
        events_without_start_time = ExternalEvent.objects.filter(start_time__isnull=True)
        
        if not events_without_start_time.exists():
            self.stdout.write('  ✅ No external events found with None start_time')
            return
        
        self.stdout.write(f'  🔧 Found {events_without_start_time.count()} external events with None start_time')
        
        fixed_count = 0
        for event in events_without_start_time:
            # Set start_time to now and end_time to 2 hours later
            now = timezone.now()
            event.start_time = now
            if not event.end_time:
                event.end_time = now + timedelta(hours=2)
            event.save()
            fixed_count += 1
            self.stdout.write(f'    ✅ Fixed external event "{event.title}"')
        
        self.stdout.write(f'  ✅ Fixed {fixed_count} external events')
