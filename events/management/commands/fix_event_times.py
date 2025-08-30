from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event
from datetime import timedelta

class Command(BaseCommand):
    help = 'Fix events with None end_time by setting a default value'

    def handle(self, *args, **options):
        # Find events with None end_time
        events_without_end_time = Event.objects.filter(end_time__isnull=True)
        
        if not events_without_end_time.exists():
            self.stdout.write(
                self.style.SUCCESS('No events found with None end_time. All good!')
            )
            return
        
        self.stdout.write(
            f'Found {events_without_end_time.count()} events with None end_time. Fixing...'
        )
        
        fixed_count = 0
        for event in events_without_end_time:
            if event.start_time:
                # Set end_time to 2 hours after start_time if start_time exists
                event.end_time = event.start_time + timedelta(hours=2)
                event.save()
                fixed_count += 1
                self.stdout.write(
                    f'Fixed event "{event.title}" - set end_time to {event.end_time}'
                )
            else:
                # If both start_time and end_time are None, set both to now
                now = timezone.now()
                event.start_time = now
                event.end_time = now + timedelta(hours=2)
                event.save()
                fixed_count += 1
                self.stdout.write(
                    f'Fixed event "{event.title}" - set start_time to {event.start_time} and end_time to {event.end_time}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fixed {fixed_count} events with None end_time.'
            )
        )
