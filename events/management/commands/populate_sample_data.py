from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from events.models import EventCategory, EventTag, Event
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample event data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample categories
        categories_data = [
            {'name': 'Technology', 'description': 'Tech meetups, conferences, and workshops'},
            {'name': 'Business', 'description': 'Business networking and professional development'},
            {'name': 'Arts & Culture', 'description': 'Art exhibitions, cultural events, and performances'},
            {'name': 'Sports & Fitness', 'description': 'Sports events, fitness classes, and outdoor activities'},
            {'name': 'Education', 'description': 'Educational workshops, seminars, and training sessions'},
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = EventCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            created_categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create sample tags
        tags_data = [
            'Conference', 'Workshop', 'Networking', 'Meetup', 'Seminar',
            'Training', 'Exhibition', 'Performance', 'Concert', 'Festival',
            'Hackathon', 'Panel Discussion', 'Q&A Session', 'Demo Day'
        ]
        
        created_tags = []
        for tag_name in tags_data:
            tag, created = EventTag.objects.get_or_create(name=tag_name)
            created_tags.append(tag)
            if created:
                self.stdout.write(f'Created tag: {tag.name}')
        
        # Create sample users if they don't exist
        organizer, created = User.objects.get_or_create(
            username='organizer1',
            defaults={
                'email': 'organizer1@example.com',
                'is_organizer': True,
                'first_name': 'John',
                'last_name': 'Organizer'
            }
        )
        if created:
            organizer.set_password('password123')
            organizer.save()
            self.stdout.write(f'Created organizer user: {organizer.username}')
        
        regular_user, created = User.objects.get_or_create(
            username='user1',
            defaults={
                'email': 'user1@example.com',
                'is_organizer': False,
                'first_name': 'Jane',
                'last_name': 'User'
            }
        )
        if created:
            regular_user.set_password('password123')
            regular_user.save()
            self.stdout.write(f'Created regular user: {regular_user.username}')
        
        # Create sample events
        events_data = [
            {
                'title': 'Tech Meetup 2024',
                'description': 'Join us for an evening of tech talks, networking, and pizza!',
                'location': 'Tech Hub, Downtown',
                'start_time': timezone.now() + timedelta(days=7),
                'end_time': timezone.now() + timedelta(days=7, hours=3),
                'max_attendees': 50,
                'category': created_categories[0],  # Technology
                'tags': ['Meetup', 'Networking', 'Tech'],
            },
            {
                'title': 'Business Networking Breakfast',
                'description': 'Start your day with coffee, breakfast, and valuable business connections.',
                'location': 'Business Center, Midtown',
                'start_time': timezone.now() + timedelta(days=3, hours=8),
                'end_time': timezone.now() + timedelta(days=3, hours=10),
                'max_attendees': 30,
                'category': created_categories[1],  # Business
                'tags': ['Networking', 'Business', 'Breakfast'],
            },
            {
                'title': 'Art Gallery Opening',
                'description': 'Experience the latest contemporary art exhibition with live music.',
                'location': 'Modern Art Gallery, Arts District',
                'start_time': timezone.now() + timedelta(days=14),
                'end_time': timezone.now() + timedelta(days=14, hours=4),
                'max_attendees': 100,
                'category': created_categories[2],  # Arts & Culture
                'tags': ['Exhibition', 'Art', 'Performance'],
            },
            {
                'title': 'Fitness Bootcamp',
                'description': 'High-intensity workout session for all fitness levels.',
                'location': 'Central Park, Fitness Area',
                'start_time': timezone.now() + timedelta(days=1, hours=6),
                'end_time': timezone.now() + timedelta(days=1, hours=7),
                'max_attendees': 25,
                'category': created_categories[3],  # Sports & Fitness
                'tags': ['Fitness', 'Workout', 'Outdoor'],
            },
            {
                'title': 'Python Programming Workshop',
                'description': 'Learn Python basics and build your first web application.',
                'location': 'Code Academy, Tech District',
                'start_time': timezone.now() + timedelta(days=21),
                'end_time': timezone.now() + timedelta(days=21, hours=6),
                'max_attendees': 20,
                'category': created_categories[0],  # Technology
                'tags': ['Workshop', 'Programming', 'Python'],
            },
        ]
        
        for event_data in events_data:
            tags = event_data.pop('tags')
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                defaults={
                    **event_data,
                    'created_by': organizer
                }
            )
            
            if created:
                # Add tags
                tag_objects = [tag for tag in created_tags if tag.name in tags]
                event.tags.set(tag_objects)
                self.stdout.write(f'Created event: {event.title}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write(f'Created {len(created_categories)} categories')
        self.stdout.write(f'Created {len(created_tags)} tags')
        self.stdout.write(f'Created {len(events_data)} events')
        self.stdout.write(f'Created users: {organizer.username}, {regular_user.username}')
        self.stdout.write('\nSample login credentials:')
        self.stdout.write('Organizer: organizer1 / password123')
        self.stdout.write('User: user1 / password123')
