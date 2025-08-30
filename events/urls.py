from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, admin_views, organizer_views

# Main router for public and authenticated user endpoints
router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'categories', views.EventCategoryViewSet, basename='category')
router.register(r'tags', views.EventTagViewSet, basename='tag')
router.register(r'reviews', views.ReviewViewSet, basename='review')

# Admin router for admin-only endpoints
admin_router = DefaultRouter()
admin_router.register(r'admin/events', admin_views.AdminEventViewSet, basename='admin-event')
admin_router.register(r'admin/categories', admin_views.AdminCategoryViewSet, basename='admin-category')
admin_router.register(r'admin/tags', admin_views.AdminTagViewSet, basename='admin-tag')

# Organizer router for organizer-specific endpoints
organizer_router = DefaultRouter()
organizer_router.register(r'organizer/events', organizer_views.OrganizerEventViewSet, basename='organizer-event')

# URL patterns organized by access level
urlpatterns = [
    # Public and authenticated user endpoints
    path('', include(router.urls)),
    
    # Admin-only endpoints (require admin privileges)
    path('', include(admin_router.urls)),
    
    # Organizer-specific endpoints (require organizer privileges)
    path('', include(organizer_router.urls)),
]

# API endpoint documentation and categorization
"""
API Endpoints by Access Level:

PUBLIC ENDPOINTS (No authentication required):
- GET /events/ - List all events
- GET /events/{id}/ - Get event details
- GET /categories/ - List event categories
- GET /tags/ - List event tags

AUTHENTICATED USER ENDPOINTS (Login required):
- GET /events/{id}/attendees/ - Get event attendees (limited data)
- GET /events/{id}/rsvp_status/ - Get user's RSVP status
- GET /events/{id}/stats/ - Get event statistics (basic)
- POST /reviews/ - Create event review
- GET /reviews/ - List event reviews

ORGANIZER ENDPOINTS (Organizer role required):
- POST /events/ - Create new event
- PUT/PATCH /events/{id}/ - Update own events
- DELETE /events/{id}/ - Delete own events
- GET /organizer/events/ - List own events
- GET /organizer/events/organizer_dashboard/ - Organizer dashboard
- GET /organizer/events/event_analytics/ - Event analytics
- GET /organizer/events/{id}/event_insights/ - Event insights
- GET /organizer/events/{id}/attendee_list/ - Detailed attendee list
- GET /organizer/events/upcoming_events/ - Upcoming events
- GET /organizer/events/past_events/ - Past events

ADMIN ENDPOINTS (Staff/Superuser required):
- GET /admin/events/ - List all events (admin view)
- GET /admin/events/dashboard_stats/ - Admin dashboard statistics
- GET /admin/events/user_analytics/ - User analytics
- GET /admin/events/event_analytics/ - Event analytics
- GET /admin/events/{id}/detailed_stats/ - Detailed event statistics
- GET /admin/categories/ - Manage categories
- GET /admin/categories/usage_stats/ - Category usage statistics
- GET /admin/tags/ - Manage tags
- GET /admin/tags/usage_stats/ - Tag usage statistics

ENHANCED DATA ACCESS:
- Public users: Basic event information
- Authenticated users: Basic event + RSVP data
- Organizers: Enhanced data for their own events
- Admins: Full access to all data and analytics
"""
