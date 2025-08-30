from django.core.management.base import BaseCommand
from django.utils import timezone
from external_events.models import ExternalEvent
from datetime import timedelta

class Command(BaseCommand):
    help = 'Fix external events with None start_time by setting a default value'

    def handle(self, *args, **options):
        # Find external events with None start_time
        events_without_start_time = ExternalEvent.objects.filter(start_time__isnull=True)
        
        if not events_without_start_time.exists():
            self.stdout.write(
                self.style.SUCCESS('No external events found with None start_time. All good!')
            )
            return
        
        self.stdout.write(
            f'Found {events_without_start_time.count()} external events with None start_time. Fixing...'
        )
        
        fixed_count = 0
        for event in events_without_start_time:
            # Set start_time to now and end_time to 2 hours later
            now = timezone.now()
            event.start_time = now
            if not event.end_time:
                event.end_time = now + timedelta(hours=2)
            event.save()
            fixed_count += 1
            self.stdout.write(
                f'Fixed external event "{event.title}" - set start_time to {event.start_time}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fixed {fixed_count} external events with None start_time.'
            )
        )
