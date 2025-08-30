"""
Test file demonstrating the permission system and access control.
This file shows how to test different permission scenarios.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Event, EventCategory, EventTag
from .permissions import (
    IsOrganizerOrReadOnly, IsEventOwnerOrReadOnly, CanReviewEvent,
    IsAdminUser, IsOrganizer, IsAdminOrOrganizer, IsAdminOrEventOwner,
    IsAdminOrOrganizerOrEventOwner
)

User = get_user_model()


class PermissionTestCase(TestCase):
    """Base test case for permission testing."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.public_user = None  # No user (public access)
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='testpass123'
        )
        self.organizer_user = User.objects.create_user(
            username='organizer_user',
            email='organizer@example.com',
            password='testpass123',
            is_organizer=True
        )
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test categories and tags
        self.category = EventCategory.objects.create(name='Test Category')
        self.tag = EventTag.objects.create(name='Test Tag')
        
        # Create test events
        self.public_event = Event.objects.create(
            title='Public Event',
            description='A public event',
            start_time='2024-12-31T23:59:59Z',
            location='Test Location',
            created_by=self.organizer_user,
            category=self.category
        )
        
        self.private_event = Event.objects.create(
            title='Private Event',
            description='A private event',
            start_time='2024-12-31T23:59:59Z',
            location='Test Location',
            created_by=self.regular_user,
            category=self.category
        )


class PermissionClassTests(PermissionTestCase):
    """Test individual permission classes."""
    
    def test_is_organizer_or_read_only(self):
        """Test IsOrganizerOrReadOnly permission."""
        permission = IsOrganizerOrReadOnly()
        
        # Test read permissions (should always be True)
        self.assertTrue(permission.has_permission(None, None))
        
        # Test write permissions for organizer
        request = type('Request', (), {'user': self.organizer_user, 'method': 'POST'})()
        self.assertTrue(permission.has_permission(request, None))
        
        # Test write permissions for regular user
        request = type('Request', (), {'user': self.regular_user, 'method': 'POST'})()
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_event_owner_or_read_only(self):
        """Test IsEventOwnerOrReadOnly permission."""
        permission = IsEventOwnerOrReadOnly()
        
        # Test read permissions (should always be True)
        self.assertTrue(permission.has_object_permission(None, None, self.public_event))
        
        # Test write permissions for event owner
        request = type('Request', (), {'user': self.organizer_user, 'method': 'PUT'})()
        self.assertTrue(permission.has_object_permission(request, None, self.public_event))
        
        # Test write permissions for non-owner
        request = type('Request', (), {'user': self.regular_user, 'method': 'PUT'})()
        self.assertFalse(permission.has_object_permission(request, None, self.public_event))
    
    def test_is_admin_user(self):
        """Test IsAdminUser permission."""
        permission = IsAdminUser()
        
        # Test admin user access
        request = type('Request', (), {'user': self.admin_user, 'method': 'GET'})()
        self.assertTrue(permission.has_permission(request, None))
        
        # Test regular user access
        request = type('Request', (), {'user': self.regular_user, 'method': 'GET'})()
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_organizer(self):
        """Test IsOrganizer permission."""
        permission = IsOrganizer()
        
        # Test organizer user access
        request = type('Request', (), {'user': self.organizer_user, 'method': 'GET'})()
        self.assertTrue(permission.has_permission(request, None))
        
        # Test regular user access
        request = type('Request', (), {'user': self.regular_user, 'method': 'GET'})()
        self.assertFalse(permission.has_permission(request, None))


class APIEndpointTests(APITestCase):
    """Test API endpoints with different permission levels."""
    
    def setUp(self):
        """Set up test data for API tests."""
        # Create test users
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='testpass123'
        )
        self.organizer_user = User.objects.create_user(
            username='organizer_user',
            email='organizer@example.com',
            password='testpass123',
            is_organizer=True
        )
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test data
        self.category = EventCategory.objects.create(name='Test Category')
        self.event = Event.objects.create(
            title='Test Event',
            description='A test event',
            start_time='2024-12-31T23:59:59Z',
            location='Test Location',
            created_by=self.organizer_user,
            category=self.category
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_public_event_access(self):
        """Test public access to event endpoints."""
        # Test public event list
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test public event detail
        response = self.client.get(f'/events/{self.event.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_authenticated_user_access(self):
        """Test authenticated user access to enhanced endpoints."""
        # Login as regular user
        self.client.force_authenticate(user=self.regular_user)
        
        # Test authenticated access to stats
        response = self.client.get(f'/events/{self.event.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test authenticated access to attendees
        response = self.client.get(f'/events/{self.event.id}/attendees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_organizer_access(self):
        """Test organizer access to management endpoints."""
        # Login as organizer
        self.client.force_authenticate(user=self.organizer_user)
        
        # Test organizer dashboard
        response = self.client.get('/organizer/events/organizer_dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test event insights
        response = self.client.get(f'/organizer/events/{self.event.id}/event_insights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_access(self):
        """Test admin access to administrative endpoints."""
        # Login as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Test admin dashboard stats
        response = self.client.get('/admin/events/dashboard_stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test user analytics
        response = self.client.get('/admin/events/user_analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthorized_access(self):
        """Test unauthorized access attempts."""
        # Test accessing organizer endpoints as regular user
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/organizer/events/organizer_dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test accessing admin endpoints as regular user
        response = self.client.get('/admin/events/dashboard_stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test accessing admin endpoints as organizer
        self.client.force_authenticate(user=self.organizer_user)
        response = self.client.get('/admin/events/dashboard_stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DataAccessTests(PermissionTestCase):
    """Test role-based data access patterns."""
    
    def test_public_data_access(self):
        """Test that public users get limited data."""
        # This would be tested in actual API calls
        # Public users should only see basic event information
        pass
    
    def test_authenticated_user_data_access(self):
        """Test that authenticated users get enhanced data."""
        # Authenticated users should see RSVP data and personal information
        pass
    
    def test_organizer_data_access(self):
        """Test that organizers get enhanced data for their events."""
        # Organizers should see detailed analytics for their own events
        pass
    
    def test_admin_data_access(self):
        """Test that admins get full data access."""
        # Admins should see all data and system-wide analytics
        pass


# Example usage and testing patterns
if __name__ == '__main__':
    print("Permission System Test Examples")
    print("=" * 40)
    print()
    print("1. Run permission class tests:")
    print("   python manage.py test events.test_permissions.PermissionClassTests")
    print()
    print("2. Run API endpoint tests:")
    print("   python manage.py test events.test_permissions.APIEndpointTests")
    print()
    print("3. Run data access tests:")
    print("   python manage.py test events.test_permissions.DataAccessTests")
    print()
    print("4. Run all tests:")
    print("   python manage.py test events.test_permissions")
    print()
    print("Note: These tests demonstrate the permission system.")
    print("Make sure to run them in a test environment.")
