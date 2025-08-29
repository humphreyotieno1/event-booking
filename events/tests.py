from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from .models import Event, EventCategory, EventTag, Review
from .serializers import EventSerializer, EventCreateSerializer

User = get_user_model()

class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_organizer=True
        )
        self.category = EventCategory.objects.create(
            name='Technology',
            description='Tech events'
        )
        self.tag = EventTag.objects.create(name='Workshop')
        
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            created_by=self.user,
            max_attendees=50,
            category=self.category
        )
        self.event.tags.add(self.tag)
    
    def test_event_creation(self):
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.created_by, self.user)
        self.assertEqual(self.event.category, self.category)
        self.assertIn(self.tag, self.event.tags.all())
    
    def test_event_properties(self):
        self.assertFalse(self.event.is_past)
        self.assertFalse(self.event.is_full)
        self.assertEqual(self.event.current_attendee_count, 0)
        self.assertEqual(self.event.available_spots, 50)
    
    def test_past_event(self):
        past_event = Event.objects.create(
            title='Past Event',
            description='Past Description',
            location='Past Location',
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(days=1, hours=2),
            created_by=self.user
        )
        self.assertTrue(past_event.is_past)
    
    def test_event_string_representation(self):
        self.assertEqual(str(self.event), 'Test Event')

class EventSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_organizer=True
        )
        self.category = EventCategory.objects.create(
            name='Technology',
            description='Tech events'
        )
        self.tag = EventTag.objects.create(name='Workshop')
        
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            created_by=self.user,
            max_attendees=50,
            category=self.category
        )
        self.event.tags.add(self.tag)
    
    def test_event_serializer(self):
        serializer = EventSerializer(self.event)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Test Event')
        self.assertEqual(data['description'], 'Test Description')
        self.assertEqual(data['location'], 'Test Location')
        self.assertEqual(data['max_attendees'], 50)
        self.assertEqual(data['category']['name'], 'Technology')
        self.assertEqual(len(data['tags']), 1)
        self.assertEqual(data['tags'][0]['name'], 'Workshop')
    
    def test_event_create_serializer(self):
        data = {
            'title': 'New Event',
            'description': 'New Description',
            'location': 'New Location',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=2, hours=3)).isoformat(),
            'max_attendees': 100,
            'category_id': self.category.id,
            'tag_ids': [self.tag.id]
        }
        
        serializer = EventCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

class EventViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_organizer=True
        )
        self.category = EventCategory.objects.create(
            name='Technology',
            description='Tech events'
        )
        self.tag = EventTag.objects.create(name='Workshop')
        
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            created_by=self.user,
            max_attendees=50,
            category=self.category
        )
        self.event.tags.add(self.tag)
        
        self.client.force_authenticate(user=self.user)
    
    def test_list_events(self):
        url = '/api/events/events/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_event(self):
        url = '/api/events/events/'
        data = {
            'title': 'New Event',
            'description': 'New Description',
            'location': 'New Location',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=2, hours=3)).isoformat(),
            'max_attendees': 100,
            'category_id': self.category.id,
            'tag_ids': [self.tag.id]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 2)
    
    def test_retrieve_event(self):
        url = f'/api/events/events/{self.event.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Event')
    
    def test_update_event(self):
        url = f'/api/events/events/{self.event.id}/'
        data = {'title': 'Updated Event'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'Updated Event')
    
    def test_delete_event(self):
        url = f'/api/events/events/{self.event.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Event.objects.count(), 0)
    
    def test_event_attendees(self):
        url = f'/api/events/events/{self.event.id}/attendees/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No attendees yet
    
    def test_event_stats(self):
        url = f'/api/events/events/{self.event.id}/stats/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_rsvps'], 0)
        self.assertEqual(response.data['going_count'], 0)
        self.assertFalse(response.data['is_full'])

class EventCategoryTest(TestCase):
    def setUp(self):
        self.category = EventCategory.objects.create(
            name='Technology',
            description='Tech events and meetups'
        )
    
    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Technology')
        self.assertEqual(self.category.description, 'Tech events and meetups')
    
    def test_category_string_representation(self):
        self.assertEqual(str(self.category), 'Technology')

class EventTagTest(TestCase):
    def setUp(self):
        self.tag = EventTag.objects.create(name='Workshop')
    
    def test_tag_creation(self):
        self.assertEqual(self.tag.name, 'Workshop')
    
    def test_tag_string_representation(self):
        self.assertEqual(str(self.tag), 'Workshop')

class ReviewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123',
            is_organizer=True
        )
        
        self.event = Event.objects.create(
            title='Past Event',
            description='Past Description',
            location='Past Location',
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=2, hours=2),
            created_by=self.organizer
        )
        
        # Create RSVP to simulate attendance
        from rsvp.models import RSVP
        self.rsvp = RSVP.objects.create(
            user=self.user,
            event=self.event,
            status='going'
        )
    
    def test_review_creation(self):
        review = Review.objects.create(
            user=self.user,
            event=self.event,
            rating=5,
            comment='Great event!'
        )
        
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Great event!')
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.event, self.event)
    
    def test_review_string_representation(self):
        review = Review.objects.create(
            user=self.user,
            event=self.event,
            rating=4,
            comment='Good event'
        )
        
        expected = f"{self.user.username} - {self.event.title} (4/5)"
        self.assertEqual(str(review), expected)
