# External Events App Documentation

## Overview

The External Events app provides integration with external event APIs (such as Ticketmaster, SeatGeek, and Eventbrite) to enrich the platform with real-world events. It enables users to discover external events and organizers to import them into the local system.

## 🏗️ **Architecture**

### **App Structure**
```
external_events/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py               # App configuration
├── models.py             # External event models
├── serializers.py        # DRF serializers for external events
├── views.py              # External event management views
├── services.py           # External API integration services
├── tasks.py              # Background tasks for data sync
├── urls.py               # URL routing
├── tests.py              # Test suite
└── README.md             # This file
```

### **Dependencies**
- Django REST Framework
- Django Extensions
- Requests (for HTTP API calls)
- Celery (for background tasks)
- Events app (for local event integration)

## 📊 **Data Models**

### **ExternalEvent Model**
```python
class ExternalEvent(models.Model):
    SOURCE_CHOICES = [
        ('ticketmaster', 'Ticketmaster'),
        ('seatgeek', 'SeatGeek'),
        ('eventbrite', 'Eventbrite'),
        ('meetup', 'Meetup'),
    ]
    
    external_id = models.CharField(max_length=100, unique=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    venue_name = models.CharField(max_length=200, blank=True)
    venue_address = models.TextField(blank=True)
    venue_city = models.CharField(max_length=100, blank=True)
    venue_state = models.CharField(max_length=100, blank=True)
    venue_country = models.CharField(max_length=100, blank=True)
    venue_postal_code = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=100, blank=True)
    subcategory = models.CharField(max_length=100, blank=True)
    price_range = models.CharField(max_length=50, blank=True)
    ticket_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    is_imported = models.BooleanField(default=False)
    imported_event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['source', 'start_time']),
            models.Index(fields=['venue_city', 'start_time']),
            models.Index(fields=['category', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.source})"
```

**Key Features**:
- **Multi-Source Support**: Integration with multiple external APIs
- **Comprehensive Data**: Rich event information including venue details
- **Import Tracking**: Track which events have been imported locally
- **Performance Indexes**: Optimized database queries for common filters

### **ExternalEventCategory Model**
```python
class ExternalEventCategory(models.Model):
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=20, choices=ExternalEvent.SOURCE_CHOICES)
    external_id = models.CharField(max_length=100, blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ['name', 'source']
    
    def __str__(self):
        return f"{self.name} ({self.source})"
```

## 🔌 **External API Integration**

### **API Service Base Class**
```python
class BaseExternalAPIService:
    """Base class for external API integrations."""
    
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(self.get_default_headers())
    
    def get_default_headers(self):
        """Get default headers for API requests."""
        return {
            'User-Agent': 'EventBooking/1.0',
            'Accept': 'application/json',
        }
    
    def make_request(self, endpoint, params=None):
        """Make HTTP request to external API."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def search_events(self, query, location=None, date_from=None, date_to=None, **kwargs):
        """Search for events. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def get_event_details(self, event_id):
        """Get detailed event information. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def get_categories(self):
        """Get available event categories. Must be implemented by subclasses."""
        raise NotImplementedError
```

### **Ticketmaster Integration**
```python
class TicketmasterService(BaseExternalAPIService):
    """Ticketmaster API integration service."""
    
    def __init__(self, api_key):
        super().__init__(api_key, 'https://app.ticketmaster.com/discovery/v2/')
        self.api_key = api_key
    
    def get_default_headers(self):
        headers = super().get_default_headers()
        return headers
    
    def search_events(self, query, location=None, date_from=None, date_to=None, **kwargs):
        """Search for events on Ticketmaster."""
        params = {
            'apikey': self.api_key,
            'keyword': query,
            'size': kwargs.get('size', 50),
            'sort': 'date,asc'
        }
        
        if location:
            params['city'] = location
        
        if date_from:
            params['startDateTime'] = date_from.isoformat()
        
        if date_to:
            params['endDateTime'] = date_to.isoformat()
        
        response = self.make_request('events.json', params)
        return self.parse_events_response(response)
    
    def parse_events_response(self, response):
        """Parse Ticketmaster API response."""
        events = []
        for event_data in response.get('_embedded', {}).get('events', []):
            event = {
                'external_id': event_data['id'],
                'source': 'ticketmaster',
                'title': event_data['name'],
                'description': event_data.get('info', ''),
                'start_time': event_data['dates']['start']['dateTime'],
                'venue_name': event_data['_embedded']['venues'][0]['name'],
                'venue_address': event_data['_embedded']['venues'][0].get('address', {}),
                'category': event_data['classifications'][0]['segment']['name'],
                'ticket_url': event_data['url'],
                'image_url': event_data.get('images', [{}])[0].get('url', ''),
            }
            events.append(event)
        
        return events
```

### **SeatGeek Integration**
```python
class SeatGeekService(BaseExternalAPIService):
    """SeatGeek API integration service."""
    
    def __init__(self, client_id):
        super().__init__(client_id, 'https://api.seatgeek.com/2/')
        self.client_id = client_id
    
    def search_events(self, query, location=None, date_from=None, date_to=None, **kwargs):
        """Search for events on SeatGeek."""
        params = {
            'client_id': self.client_id,
            'q': query,
            'per_page': kwargs.get('size', 50),
            'sort': 'score.desc'
        }
        
        if location:
            params['venue.city'] = location
        
        if date_from:
            params['datetime_utc.gte'] = date_from.isoformat()
        
        if date_to:
            params['datetime_utc.lte'] = date_to.isoformat()
        
        response = self.make_request('events', params)
        return self.parse_events_response(response)
    
    def parse_events_response(self, response):
        """Parse SeatGeek API response."""
        events = []
        for event_data in response.get('events', []):
            event = {
                'external_id': str(event_data['id']),
                'source': 'seatgeek',
                'title': event_data['title'],
                'description': event_data.get('description', ''),
                'start_time': event_data['datetime_utc'],
                'venue_name': event_data['venue']['name'],
                'venue_address': event_data['venue'].get('address', {}),
                'category': event_data.get('type', ''),
                'ticket_url': event_data['url'],
                'image_url': event_data.get('performers', [{}])[0].get('image', ''),
            }
            events.append(event)
        
        return events
```

## 🎯 **Views & Endpoints**

### **External Event Discovery Views**

#### **Search External Events**
```python
class ExternalEventSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search for external events across multiple sources."""
        query = request.query_params.get('q', '')
        source = request.query_params.get('source', 'all')
        location = request.query_params.get('location')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        category = request.query_params.get('category')
        
        if not query:
            return Response(
                {'error': 'Search query is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        if date_from:
            date_from = parse_datetime(date_from)
        if date_to:
            date_to = parse_datetime(date_to)
        
        # Search external APIs
        external_events = self.search_external_apis(
            query, source, location, date_from, date_to, category
        )
        
        # Check which events are already imported
        imported_events = self.check_imported_events(external_events)
        
        # Serialize results
        serializer = ExternalEventSerializer(external_events, many=True)
        return Response({
            'events': serializer.data,
            'imported_events': imported_events,
            'total_count': len(external_events)
        })
    
    def search_external_apis(self, query, source, location, date_from, date_to, category):
        """Search across configured external APIs."""
        events = []
        
        if source == 'all' or source == 'ticketmaster':
            if settings.TICKETMASTER_API_KEY:
                service = TicketmasterService(settings.TICKETMASTER_API_KEY)
                try:
                    ticketmaster_events = service.search_events(
                        query, location, date_from, date_to, category=category
                    )
                    events.extend(ticketmaster_events)
                except Exception as e:
                    logger.error(f"Ticketmaster API error: {e}")
        
        if source == 'all' or source == 'seatgeek':
            if settings.SEATGEEK_CLIENT_ID:
                service = SeatGeekService(settings.SEATGEEK_CLIENT_ID)
                try:
                    seatgeek_events = service.search_events(
                        query, location, date_from, date_to, category=category
                    )
                    events.extend(seatgeek_events)
                except Exception as e:
                    logger.error(f"SeatGeek API error: {e}")
        
        return events
```

#### **Get External Event Details**
```python
class ExternalEventDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, source, external_id):
        """Get detailed information about an external event."""
        try:
            external_event = ExternalEvent.objects.get(
                source=source, external_id=external_id
            )
            serializer = ExternalEventSerializer(external_event)
            return Response(serializer.data)
        except ExternalEvent.DoesNotExist:
            # Fetch from external API if not in database
            event_data = self.fetch_from_external_api(source, external_id)
            if event_data:
                return Response(event_data)
            return Response(
                {'error': 'Event not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def fetch_from_external_api(self, source, external_id):
        """Fetch event details from external API."""
        if source == 'ticketmaster':
            service = TicketmasterService(settings.TICKETMASTER_API_KEY)
            return service.get_event_details(external_id)
        elif source == 'seatgeek':
            service = SeatGeekService(settings.SEATGEEK_CLIENT_ID)
            return service.get_event_details(external_id)
        return None
```

### **Event Import Views**

#### **Import External Event**
```python
class ImportExternalEventView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizer]
    
    def post(self, request, source, external_id):
        """Import an external event into the local system."""
        try:
            external_event = ExternalEvent.objects.get(
                source=source, external_id=external_id
            )
        except ExternalEvent.DoesNotExist:
            return Response(
                {'error': 'External event not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already imported
        if external_event.is_imported:
            return Response(
                {'error': 'Event already imported'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create local event
        local_event = self.create_local_event(external_event, request.user)
        
        # Mark as imported
        external_event.is_imported = True
        external_event.imported_event = local_event
        external_event.save()
        
        # Send notification
        send_event_import_notification.delay(local_event.id, request.user.id)
        
        return Response({
            'message': 'Event imported successfully',
            'local_event_id': local_event.id,
            'local_event_url': f"/events/{local_event.id}/"
        }, status=status.HTTP_201_CREATED)
    
    def create_local_event(self, external_event, user):
        """Create a local event from external event data."""
        # Map external event data to local event model
        event_data = {
            'title': external_event.title,
            'description': external_event.description,
            'location': external_event.location,
            'start_time': external_event.start_time,
            'end_time': external_event.end_time,
            'created_by': user,
            'external_event_id': external_event.external_id,
            'external_source': external_event.source,
        }
        
        # Create event
        event = Event.objects.create(**event_data)
        
        # Add venue information if available
        if external_event.venue_name:
            event.venue_name = external_event.venue_name
            event.venue_address = external_event.venue_address
            event.save()
        
        return event
```

## 🔄 **Data Synchronization**

### **Background Sync Tasks**
```python
@shared_task
def sync_external_events():
    """Synchronize external events data."""
    sources = ['ticketmaster', 'seatgeek']
    
    for source in sources:
        try:
            if source == 'ticketmaster' and settings.TICKETMASTER_API_KEY:
                sync_ticketmaster_events.delay()
            elif source == 'seatgeek' and settings.SEATGEEK_CLIENT_ID:
                sync_seatgeek_events.delay()
        except Exception as e:
            logger.error(f"Error syncing {source} events: {e}")

@shared_task
def sync_ticketmaster_events():
    """Synchronize Ticketmaster events."""
    service = TicketmasterService(settings.TICKETMASTER_API_KEY)
    
    # Get popular categories
    categories = ['music', 'sports', 'arts', 'family']
    
    for category in categories:
        try:
            events = service.search_events(
                query=category, 
                size=100,
                date_from=timezone.now(),
                date_to=timezone.now() + timedelta(days=90)
            )
            
            for event_data in events:
                ExternalEvent.objects.update_or_create(
                    external_id=event_data['external_id'],
                    source='ticketmaster',
                    defaults=event_data
                )
        except Exception as e:
            logger.error(f"Error syncing Ticketmaster {category} events: {e}")

@shared_task
def sync_seatgeek_events():
    """Synchronize SeatGeek events."""
    service = SeatGeekService(settings.SEATGEEK_CLIENT_ID)
    
    # Get popular categories
    categories = ['concert', 'sports', 'theater', 'comedy']
    
    for category in categories:
        try:
            events = service.search_events(
                query=category, 
                size=100,
                date_from=timezone.now(),
                date_to=timezone.now() + timedelta(days=90)
            )
            
            for event_data in events:
                ExternalEvent.objects.update_or_create(
                    external_id=event_data['external_id'],
                    source='seatgeek',
                    defaults=event_data
                )
        except Exception as e:
            logger.error(f"Error syncing SeatGeek {category} events: {e}")
```

### **Sync Configuration**
```python
# Celery Beat schedule for external event synchronization
CELERY_BEAT_SCHEDULE = {
    'sync-external-events': {
        'task': 'external_events.tasks.sync_external_events',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'sync-ticketmaster-events': {
        'task': 'external_events.tasks.sync_ticketmaster_events',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'sync-seatgeek-events': {
        'task': 'external_events.tasks.sync_seatgeek_events',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM
    },
}
```

## 📊 **Analytics & Reporting**

### **External Event Analytics**
```python
class ExternalEventAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get analytics about external events."""
        # Source distribution
        source_stats = ExternalEvent.objects.values('source').annotate(
            count=Count('id'),
            imported_count=Count('id', filter=Q(is_imported=True))
        )
        
        # Category distribution
        category_stats = ExternalEvent.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Import statistics
        import_stats = {
            'total_external_events': ExternalEvent.objects.count(),
            'total_imported': ExternalEvent.objects.filter(is_imported=True).count(),
            'import_rate': (ExternalEvent.objects.filter(is_imported=True).count() / 
                           max(ExternalEvent.objects.count(), 1)) * 100
        }
        
        # Recent activity
        recent_imports = ExternalEvent.objects.filter(
            is_imported=True
        ).select_related('imported_event').order_by('-updated_at')[:10]
        
        return Response({
            'source_stats': list(source_stats),
            'category_stats': list(category_stats),
            'import_stats': import_stats,
            'recent_imports': ExternalEventSerializer(recent_imports, many=True).data
        })
```

### **Import Performance Metrics**
- **Import Success Rate**: Percentage of successful imports
- **Source Performance**: API response times and success rates
- **Category Popularity**: Most imported event categories
- **Geographic Distribution**: Import patterns by location

## 🚀 **Performance Optimizations**

### **Database Optimizations**
```python
# Optimized external event queries
external_events = ExternalEvent.objects.select_related(
    'imported_event'
).filter(
    source=source,
    start_time__gte=timezone.now()
).order_by('start_time')

# Efficient counting with annotations
source_stats = ExternalEvent.objects.values('source').annotate(
    count=Count('id'),
    imported_count=Count('id', filter=Q(is_imported=True))
)
```

### **Caching Strategy**
- **API Responses**: Cache external API responses
- **Search Results**: Cache search queries and results
- **Event Details**: Cache frequently accessed event information

### **Background Processing**
- **Data Synchronization**: Asynchronous external API sync
- **Event Import**: Background event creation and processing
- **Notification Sending**: Asynchronous import notifications

## 🧪 **Testing**

### **Test Structure**
```
tests/
├── test_models.py          # External event model tests
├── test_views.py           # View and endpoint tests
├── test_services.py        # External API service tests
├── test_integration.py     # Integration tests
├── test_sync.py            # Synchronization tests
└── test_import.py          # Import functionality tests
```

### **Running Tests**
```bash
# Test specific components
python manage.py test external_events.test_models
python manage.py test external_events.test_services
python manage.py test external_events.test_sync

# Test entire app
python manage.py test external_events

# Test with coverage
coverage run --source='external_events' manage.py test external_events
coverage report
```

### **Test Examples**
```python
def test_external_event_creation(self):
    """Test external event model creation."""
    external_event = ExternalEvent.objects.create(
        external_id='test123',
        source='ticketmaster',
        title='Test Concert',
        start_time=timezone.now() + timedelta(days=1),
        location='Test Venue'
    )
    
    self.assertEqual(external_event.title, 'Test Concert')
    self.assertEqual(external_event.source, 'ticketmaster')
    self.assertFalse(external_event.is_imported)

def test_event_import(self):
    """Test importing external event to local system."""
    external_event = ExternalEvent.objects.create(
        external_id='test123',
        source='ticketmaster',
        title='Test Concert',
        start_time=timezone.now() + timedelta(days=1),
        location='Test Venue'
    )
    
    # Import event
    response = self.client.post(
        f'/external-events/{external_event.source}/{external_event.external_id}/import/',
        {},
        HTTP_AUTHORIZATION=f'Bearer {self.organizer_token}'
    )
    
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertTrue(ExternalEvent.objects.get(id=external_event.id).is_imported)
```

## 🔧 **Configuration**

### **Settings Integration**
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'external_events',
]

# External API settings
TICKETMASTER_API_KEY = os.getenv('TICKETMASTER_API_KEY')
SEATGEEK_CLIENT_ID = os.getenv('SEATGEEK_CLIENT_ID')
EVENTBRITE_API_KEY = os.getenv('EVENTBRITE_API_KEY')

# External events settings
EXTERNAL_EVENTS_SETTINGS = {
    'SYNC_INTERVAL_HOURS': 24,
    'MAX_EVENTS_PER_SYNC': 1000,
    'ENABLE_AUTO_SYNC': True,
    'CACHE_DURATION_MINUTES': 60,
}
```

### **URL Configuration**
```python
# Main app URLs
urlpatterns = [
    path('external-events/', include('external_events.urls')),
]
```

## 📚 **API Documentation**

### **External Event Endpoints**

#### **Search External Events**
```bash
GET /external-events/search/?q=concert&source=ticketmaster&location=New York
Authorization: Bearer <jwt_token>

# Response
{
    "events": [
        {
            "external_id": "12345",
            "source": "ticketmaster",
            "title": "Rock Concert 2024",
            "description": "Amazing rock concert",
            "start_time": "2024-12-31T20:00:00Z",
            "venue_name": "Madison Square Garden",
            "category": "Music",
            "ticket_url": "https://ticketmaster.com/event/12345"
        }
    ],
    "imported_events": [],
    "total_count": 1
}
```

#### **Get External Event Details**
```bash
GET /external-events/ticketmaster/12345/
Authorization: Bearer <jwt_token>

# Response
{
    "external_id": "12345",
    "source": "ticketmaster",
    "title": "Rock Concert 2024",
    "description": "Amazing rock concert",
    "start_time": "2024-12-31T20:00:00Z",
    "end_time": "2024-12-31T23:00:00Z",
    "venue_name": "Madison Square Garden",
    "venue_address": "4 Pennsylvania Plaza",
    "venue_city": "New York",
    "venue_state": "NY",
    "category": "Music",
    "subcategory": "Rock",
    "price_range": "$50-$200",
    "ticket_url": "https://ticketmaster.com/event/12345",
    "image_url": "https://example.com/image.jpg",
    "is_imported": false
}
```

#### **Import External Event**
```bash
POST /external-events/ticketmaster/12345/import/
Authorization: Bearer <organizer_jwt_token>
Content-Type: application/json

# Response
{
    "message": "Event imported successfully",
    "local_event_id": 789,
    "local_event_url": "/events/789/"
}
```

## 🚨 **Error Handling**

### **Common Error Responses**
```python
# API Rate Limit Error
{
    "error": "External API rate limit exceeded. Please try again later.",
    "status_code": 429,
    "retry_after": 3600
}

# API Unavailable Error
{
    "error": "External API temporarily unavailable. Please try again later.",
    "status_code": 503,
    "retry_after": 300
}

# Import Validation Error
{
    "error": "Cannot import event. Event data validation failed.",
    "status_code": 400,
    "details": {
        "start_time": ["Start time must be in the future"]
    }
}
```

### **Custom Exception Handling**
- **API Errors**: Clear external API error messages
- **Validation Errors**: Field-level import validation feedback
- **Rate Limiting**: Clear retry information
- **Network Errors**: Connection and timeout handling

## 🔮 **Future Enhancements**

### **Planned Features**
- **Additional Sources**: Integration with more event platforms
- **Advanced Filtering**: More sophisticated search and filtering
- **Real-time Updates**: WebSocket support for live data
- **Bulk Import**: Import multiple events at once

### **Integration Improvements**
- **Webhook Support**: Real-time event updates from external sources
- **Advanced Mapping**: Custom field mapping for different sources
- **Data Enrichment**: Enhance external data with local information
- **Analytics Dashboard**: Comprehensive external event analytics

### **Performance Enhancements**
- **Advanced Caching**: Redis-based caching for external data
- **Background Processing**: Asynchronous data processing
- **Database Optimization**: Advanced query optimization
- **CDN Integration**: Optimized image and media delivery

## 📞 **Support & Contributing**

### **Getting Help**
- **Documentation**: Check this README and main project README
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join GitHub Discussions for questions

### **Contributing**
- **Code Style**: Follow PEP 8 and Django conventions
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update docs for all new features
- **Security**: Follow security best practices

---

**External Events App** - The external event integration system for the Event Booking platform, providing seamless access to real-world events from multiple sources.
