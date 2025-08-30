# Events App Documentation

## Overview

The Events app is the core component of the Event Booking system, responsible for managing events, categories, tags, and reviews. It provides comprehensive event management capabilities with role-based access control and advanced analytics.

## 🏗️ **Architecture**

### **App Structure**
```
events/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py               # App configuration
├── models.py             # Data models
├── serializers.py        # DRF serializers
├── views.py              # Main views and endpoints
├── admin_views.py        # Admin-specific views
├── organizer_views.py    # Organizer-specific views
├── permissions.py        # Custom permission classes
├── urls.py               # URL routing
├── ACCESS_CONTROL_GUIDE.md  # Access control documentation
├── test_permissions.py   # Permission testing
└── README.md             # This file
```

### **Dependencies**
- Django REST Framework
- Django Filters
- Django Extensions
- Pillow (for image handling)

## 📊 **Data Models**

### **Event Model**
```python
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(EventTag, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Features**:
- **Capacity Management**: `max_attendees` with automatic full/available status
- **Categorization**: Events belong to categories and can have multiple tags
- **Recurring Events**: Support for weekly/monthly recurring events
- **Ownership**: Events are tied to their creators (organizers)

### **EventCategory Model**
```python
class EventCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### **EventTag Model**
```python
class EventTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### **Review Model**
```python
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

## 🔐 **Permission System**

### **Permission Classes**

#### **IsOrganizerOrReadOnly**
- **Purpose**: Controls event creation access
- **Access**: Organizers can create events, others read-only
- **Usage**: Applied to event creation endpoints

#### **IsEventOwnerOrReadOnly**
- **Purpose**: Controls event modification access
- **Access**: Event owners can edit/delete, others read-only
- **Usage**: Applied to event update/delete endpoints

#### **IsAdminUser**
- **Purpose**: Restricts access to admin users only
- **Access**: Staff and superusers only
- **Usage**: Applied to admin-specific endpoints

#### **IsOrganizer**
- **Purpose**: Restricts access to organizer users only
- **Access**: Users with `is_organizer=True` only
- **Usage**: Applied to organizer-specific endpoints

#### **IsAdminOrEventOwner**
- **Purpose**: Allows admin users or event owners
- **Access**: Admin users or event creators
- **Usage**: Applied to mixed-access endpoints

### **Permission Assignment Strategy**
```python
def get_permissions(self):
    if self.action in ['create', 'update', 'partial_update', 'destroy']:
        permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly, IsEventOwnerOrReadOnly]
    elif self.action in ['attendees', 'rsvp_status', 'stats']:
        permission_classes = [IsAuthenticated]
    else:
        permission_classes = [AllowAny]
    return [permission() for permission in permission_classes]
```

## 🎯 **Views & Endpoints**

### **Main EventViewSet**

#### **Public Endpoints (No Auth)**
- `GET /events/` - List all events with pagination and filtering
- `GET /events/{id}/` - Get event details

#### **Authenticated User Endpoints**
- `GET /events/{id}/attendees/` - Get event attendees (role-based data)
- `GET /events/{id}/rsvp_status/` - Check user's RSVP status
- `GET /events/{id}/stats/` - Get event statistics (role-enhanced)
- `GET /events/{id}/insights/` - Get enhanced event insights

#### **Organizer Endpoints**
- `POST /events/` - Create new event
- `PUT/PATCH /events/{id}/` - Update own events
- `DELETE /events/{id}/` - Delete own events

### **Admin Views (AdminEventViewSet)**

#### **Dashboard & Analytics**
- `GET /admin/events/dashboard_stats/` - System-wide dashboard
- `GET /admin/events/user_analytics/` - User behavior analytics
- `GET /admin/events/event_analytics/` - Event performance analytics
- `GET /admin/events/{id}/detailed_stats/` - Detailed event statistics

#### **Content Management**
- `GET /admin/categories/` - Manage event categories
- `GET /admin/tags/` - Manage event tags
- `GET /admin/categories/usage_stats/` - Category usage statistics
- `GET /admin/tags/usage_stats/` - Tag usage statistics

### **Organizer Views (OrganizerEventViewSet)**

#### **Event Management**
- `GET /organizer/events/` - List own events
- `GET /organizer/events/organizer_dashboard/` - Personal dashboard
- `GET /organizer/events/event_analytics/` - Event performance analytics

#### **Event Insights**
- `GET /organizer/events/{id}/event_insights/` - Detailed event insights
- `GET /organizer/events/{id}/attendee_list/` - Comprehensive attendee list
- `GET /organizer/events/upcoming_events/` - Upcoming events with RSVP counts
- `GET /organizer/events/past_events/` - Past events with performance metrics

## 🔍 **Search & Filtering**

### **Filter Backends**
- **DjangoFilterBackend**: Field-based filtering
- **SearchFilter**: Full-text search across multiple fields
- **OrderingFilter**: Sortable results

### **Available Filters**
```python
filterset_fields = ['category', 'tags', 'is_recurring']
search_fields = ['title', 'description', 'location']
ordering_fields = ['start_time', 'title', 'created_at']
ordering = ['-start_time']  # Default ordering
```

### **Advanced Search**
```python
# Date range filtering
?date_from=2024-01-01&date_to=2024-12-31

# Location-based search
?location=Downtown

# Organizer filtering
?organizer_id=123

# Tag-based filtering
?tag_ids=1,2,3

# Popularity sorting
?sort_by=popularity&sort_order=desc
```

## 📈 **Analytics & Insights**

### **Event Performance Metrics**
- **RSVP Statistics**: Total, going, interested, cancelled counts
- **Engagement Metrics**: Unique attendees, average RSVPs per user
- **Review Analysis**: Rating distribution, total reviews
- **Time-based Trends**: Monthly event creation and RSVP patterns

### **Organizer Analytics**
- **Event Portfolio**: Total events, upcoming vs. past
- **Performance Tracking**: Top-performing events by RSVP count
- **Category Performance**: Success rates by event category
- **Audience Insights**: Attendee demographics and behavior

### **Admin Analytics**
- **System Health**: Overall platform metrics
- **User Engagement**: Active users, organizer activity
- **Content Performance**: Popular categories and tags
- **Trend Analysis**: Platform growth and usage patterns

## 🚀 **Performance Optimizations**

### **Database Optimizations**
```python
# Optimized queryset with select_related and prefetch_related
queryset = Event.objects.select_related(
    'created_by', 'category'
).prefetch_related(
    'tags', 'reviews', 'rsvps'
)
```

### **Role-Based Data Loading**
```python
if self.request.user.is_authenticated:
    if self.request.user.is_staff or self.request.user.is_superuser:
        # Admin users get full access
        pass
    elif self.request.user.is_organizer:
        # Organizers get enhanced data for their events
        queryset = queryset.prefetch_related('rsvps')
    else:
        # Regular users get basic enhanced data
        queryset = queryset.prefetch_related('rsvps')
```

### **Caching Strategy**
- **Event Lists**: Redis-cached with pagination
- **Statistics**: Aggregated data cached for performance
- **User-Specific Data**: Personalized caching based on role

## 🧪 **Testing**

### **Test Structure**
```
test_permissions.py      # Permission system tests
test_views.py           # View and endpoint tests
test_models.py          # Model and validation tests
test_serializers.py     # Serializer tests
test_integration.py     # Integration tests
```

### **Running Tests**
```bash
# Test specific components
python manage.py test events.test_permissions.PermissionClassTests
python manage.py test events.test_permissions.APIEndpointTests
python manage.py test events.test_permissions.DataAccessTests

# Test entire app
python manage.py test events

# Test with coverage
coverage run --source='events' manage.py test events
coverage report
```

### **Test Examples**
```python
def test_organizer_access(self):
    """Test that organizers can access their dashboard."""
    self.client.force_authenticate(user=self.organizer_user)
    response = self.client.get('/organizer/events/organizer_dashboard/')
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertIn('total_events', response.data)

def test_public_event_access(self):
    """Test public access to event endpoints."""
    response = self.client.get('/events/')
    self.assertEqual(response.status_code, status.HTTP_200_OK)
```

## 🔧 **Configuration**

### **Settings Integration**
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'events',
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

### **URL Configuration**
```python
# Main app URLs
urlpatterns = [
    path('', include(router.urls)),
    path('', include(admin_router.urls)),
    path('', include(organizer_router.urls)),
]
```

## 📚 **API Documentation**

### **Swagger/OpenAPI**
- **URL**: `/swagger/` (when running)
- **Features**: Interactive API documentation
- **Authentication**: JWT token support
- **Testing**: Try endpoints directly from browser

### **Endpoint Examples**
See the main README.md for comprehensive endpoint documentation with examples.

## 🚨 **Error Handling**

### **Common Error Responses**
```python
# Permission Denied
{
    "error": "Access denied. Only event owners and admins can view insights.",
    "status_code": 403
}

# Validation Error
{
    "error": "Invalid event data",
    "details": {
        "start_time": ["Start time must be in the future"]
    }
}

# Not Found
{
    "error": "Event not found",
    "status_code": 404
}
```

### **Custom Exception Handling**
- **Permission Errors**: Clear access control messages
- **Validation Errors**: Detailed field-level feedback
- **Business Logic Errors**: Contextual error messages

## 🔮 **Future Enhancements**

### **Planned Features**
- **Real-time Updates**: WebSocket support for live event updates
- **Advanced Analytics**: Machine learning insights and predictions
- **Event Templates**: Predefined event structures for common types
- **Integration APIs**: Third-party platform integrations

### **Scalability Improvements**
- **Microservices**: Event processing as separate service
- **Event Sourcing**: Event-driven architecture for audit trails
- **CQRS**: Command Query Responsibility Segregation
- **GraphQL**: Alternative to REST for complex queries

## 📞 **Support & Contributing**

### **Getting Help**
- **Documentation**: Check this README and ACCESS_CONTROL_GUIDE.md
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join GitHub Discussions for questions

### **Contributing**
- **Code Style**: Follow PEP 8 and Django conventions
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update docs for all new features
- **Security**: Follow security best practices

---

**Events App** - The heart of the Event Booking system, providing comprehensive event management with enterprise-grade security and analytics.
