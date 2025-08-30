# RSVP App Documentation

## Overview

The RSVP app manages event attendance, RSVP status tracking, and capacity management. It provides a robust system for users to respond to events and organizers to track attendance with real-time updates and analytics.

## 🏗️ **Architecture**

### **App Structure**
```
rsvp/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py               # App configuration
├── models.py             # RSVP and attendee models
├── serializers.py        # DRF serializers for RSVP operations
├── views.py              # RSVP management views
├── urls.py               # URL routing
├── tests.py              # Test suite
└── README.md             # This file
```

### **Dependencies**
- Django REST Framework
- Django Extensions
- Events app (for event relationships)
- Accounts app (for user relationships)

## 📊 **Data Models**

### **RSVP Model**
```python
class RSVP(models.Model):
    STATUS_CHOICES = [
        ('going', 'Going'),
        ('interested', 'Interested'),
        ('cancelled', 'Cancelled'),
        ('waitlist', 'Waitlist'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rsvps')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='interested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.status})"
```

**Key Features**:
- **Status Management**: Multiple RSVP statuses (going, interested, cancelled, waitlist)
- **Unique Constraints**: One RSVP per user per event
- **Timestamps**: Creation and update tracking
- **Notes**: Optional user notes for organizers

### **Attendee Model (Derived)**
```python
# Attendee information is derived from RSVP data
# with additional computed properties
class AttendeeInfo:
    def __init__(self, rsvp):
        self.user = rsvp.user
        self.status = rsvp.status
        self.rsvp_date = rsvp.created_at
        self.is_confirmed = rsvp.status == 'going'
        self.is_waitlisted = rsvp.status == 'waitlist'
```

## 🎯 **Views & Endpoints**

### **RSVP Management Views**

#### **Create/Update RSVP**
```python
class RSVPCreateUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Check if user already has an RSVP
        existing_rsvp = RSVP.objects.filter(user=request.user, event=event).first()
        
        if existing_rsvp:
            # Update existing RSVP
            serializer = RSVPSerializer(existing_rsvp, data=request.data, partial=True)
        else:
            # Create new RSVP
            serializer = RSVPSerializer(data=request.data)
            serializer.context['event'] = event
            serializer.context['user'] = request.user
        
        if serializer.is_valid():
            rsvp = serializer.save()
            
            # Handle capacity and waitlist logic
            self.handle_capacity_management(event, rsvp)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def handle_capacity_management(self, event, rsvp):
        """Handle capacity limits and waitlist management."""
        if rsvp.status == 'going':
            if event.is_full:
                rsvp.status = 'waitlist'
                rsvp.save()
                # Send waitlist notification
                send_waitlist_notification.delay(rsvp.id)
            else:
                # Check if this RSVP moves someone from waitlist
                self.process_waitlist(event)
```

#### **RSVP Status Management**
```python
class RSVPStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        """Get user's RSVP status for an event."""
        try:
            rsvp = RSVP.objects.get(user=request.user, event_id=event_id)
            serializer = RSVPSerializer(rsvp)
            return Response(serializer.data)
        except RSVP.DoesNotExist:
            return Response({'status': 'not_rsvpd'})
    
    def put(self, request, event_id):
        """Update RSVP status."""
        rsvp = get_object_or_404(RSVP, user=request.user, event_id=event_id)
        serializer = RSVPSerializer(rsvp, data=request.data, partial=True)
        
        if serializer.is_valid():
            old_status = rsvp.status
            rsvp = serializer.save()
            
            # Handle status change effects
            self.handle_status_change(rsvp, old_status)
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def handle_status_change(self, rsvp, old_status):
        """Handle effects of RSVP status changes."""
        if old_status == 'going' and rsvp.status != 'going':
            # User cancelled attendance, check waitlist
            self.process_waitlist(rsvp.event)
        elif rsvp.status == 'going' and old_status != 'going':
            # User confirmed attendance
            if rsvp.event.is_full:
                rsvp.status = 'waitlist'
                rsvp.save()
```

### **Attendee Management Views**

#### **Event Attendees List**
```python
class EventAttendeesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        """Get list of attendees for an event with role-based access."""
        event = get_object_or_404(Event, id=event_id)
        
        # Role-based data access
        if request.user.is_staff or request.user.is_superuser:
            # Admin users get full attendee list
            attendees = event.rsvps.select_related('user').all()
        elif request.user.is_organizer and event.created_by == request.user:
            # Organizers get full attendee list for their events
            attendees = event.rsvps.select_related('user').all()
        else:
            # Regular users get basic attendee list
            attendees = event.rsvps.filter(status='going').select_related('user')
        
        serializer = AttendeeSerializer(attendees, many=True)
        return Response(serializer.data)
```

#### **Attendee Analytics**
```python
class AttendeeAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        """Get attendee analytics for an event."""
        event = get_object_or_404(Event, id=event_id)
        
        # Check access permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                (request.user.is_organizer and event.created_by == request.user)):
            return Response(
                {'error': 'Access denied. Only event owners and admins can view analytics.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate analytics
        total_rsvps = event.rsvps.count()
        going_count = event.rsvps.filter(status='going').count()
        interested_count = event.rsvps.filter(status='interested').count()
        waitlist_count = event.rsvps.filter(status='waitlist').count()
        cancelled_count = event.rsvps.filter(status='cancelled').count()
        
        # RSVP timeline
        rsvp_timeline = event.rsvps.extra(
            select={'day': "EXTRACT(day FROM created_at)"}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        analytics = {
            'total_rsvps': total_rsvps,
            'going_count': going_count,
            'interested_count': interested_count,
            'waitlist_count': waitlist_count,
            'cancelled_count': cancelled_count,
            'rsvp_timeline': list(rsvp_timeline),
            'capacity_utilization': (going_count / event.max_attendees * 100) if event.max_attendees else 0
        }
        
        return Response(analytics)
```

## 🔄 **RSVP Workflow**

### **RSVP Process Flow**
```
1. User RSVPs to Event
   ↓
2. Check Event Capacity
   ↓
3. Assign Status (Going/Waitlist)
   ↓
4. Update Event Statistics
   ↓
5. Send Notifications
   ↓
6. Handle Waitlist Processing
```

### **Capacity Management**
```python
def check_event_capacity(event):
    """Check if event has available capacity."""
    going_count = event.rsvps.filter(status='going').count()
    return going_count < event.max_attendees if event.max_attendees else True

def process_waitlist(event):
    """Process waitlist when spots become available."""
    waitlisted_rsvps = event.rsvps.filter(status='waitlist').order_by('created_at')
    
    for rsvp in waitlisted_rsvps:
        if not event.is_full:
            rsvp.status = 'going'
            rsvp.save()
            
            # Send confirmation notification
            send_waitlist_confirmation.delay(rsvp.id)
        else:
            break
```

### **Status Transitions**
```python
RSVP_STATUS_TRANSITIONS = {
    'interested': ['going', 'cancelled'],
    'going': ['interested', 'cancelled'],
    'cancelled': ['interested', 'going'],
    'waitlist': ['going', 'interested', 'cancelled']
}

def validate_status_transition(old_status, new_status):
    """Validate RSVP status transitions."""
    allowed_transitions = RSVP_STATUS_TRANSITIONS.get(old_status, [])
    return new_status in allowed_transitions
```

## 📊 **Analytics & Reporting**

### **RSVP Statistics**
```python
class RSVPStatisticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        """Get comprehensive RSVP statistics for an event."""
        event = get_object_or_404(Event, id=event_id)
        
        # Basic statistics
        stats = {
            'total_rsvps': event.rsvps.count(),
            'going_count': event.rsvps.filter(status='going').count(),
            'interested_count': event.rsvps.filter(status='interested').count(),
            'waitlist_count': event.rsvps.filter(status='waitlist').count(),
            'cancelled_count': event.rsvps.filter(status='cancelled').count(),
        }
        
        # Enhanced statistics for organizers and admins
        if request.user.is_staff or request.user.is_superuser or (
            request.user.is_organizer and event.created_by == request.user
        ):
            # RSVP trends over time
            rsvp_trends = event.rsvps.extra(
                select={'date': "DATE(created_at)"}
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            # User engagement metrics
            unique_users = event.rsvps.values('user').distinct().count()
            avg_rsvps_per_user = event.rsvps.count() / max(unique_users, 1)
            
            stats.update({
                'rsvp_trends': list(rsvp_trends),
                'unique_users': unique_users,
                'avg_rsvps_per_user': avg_rsvps_per_user,
                'capacity_utilization': (stats['going_count'] / event.max_attendees * 100) if event.max_attendees else 0
            })
        
        return Response(stats)
```

### **User RSVP History**
```python
class UserRSVPHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's RSVP history across all events."""
        user_rsvps = request.user.rsvps.select_related('event').order_by('-created_at')
        
        # Group by status
        rsvp_summary = {
            'total_rsvps': user_rsvps.count(),
            'going_count': user_rsvps.filter(status='going').count(),
            'interested_count': user_rsvps.filter(status='interested').count(),
            'cancelled_count': user_rsvps.filter(status='cancelled').count(),
            'waitlist_count': user_rsvps.filter(status='waitlist').count(),
        }
        
        # Recent RSVPs
        recent_rsvps = user_rsvps[:10]
        recent_serializer = RSVPSerializer(recent_rsvps, many=True)
        
        return Response({
            'summary': rsvp_summary,
            'recent_rsvps': recent_serializer.data
        })
```

## 🔔 **Notifications & Alerts**

### **RSVP Notifications**
```python
@shared_task
def send_rsvp_notification(rsvp_id):
    """Send notification when user RSVPs to an event."""
    rsvp = RSVP.objects.get(id=rsvp_id)
    
    if rsvp.status == 'going':
        subject = f"You're going to {rsvp.event.title}!"
        message = f"Great! You're confirmed to attend {rsvp.event.title} on {rsvp.event.start_time.strftime('%B %d, %Y')}."
    elif rsvp.status == 'waitlist':
        subject = f"You're on the waitlist for {rsvp.event.title}"
        message = f"You're on the waitlist for {rsvp.event.title}. We'll notify you if a spot becomes available."
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [rsvp.user.email])

@shared_task
def send_waitlist_confirmation(rsvp_id):
    """Send notification when waitlisted user gets confirmed."""
    rsvp = RSVP.objects.get(id=rsvp_id)
    
    subject = f"Good news! You're confirmed for {rsvp.event.title}"
    message = f"A spot has opened up! You're now confirmed to attend {rsvp.event.title} on {rsvp.event.start_time.strftime('%B %d, %Y')}."
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [rsvp.user.email])
```

### **Event Reminders**
```python
@shared_task
def send_event_reminders():
    """Send reminders to confirmed attendees before events."""
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    upcoming_events = Event.objects.filter(
        start_time__date=tomorrow,
        rsvps__status='going'
    ).distinct()
    
    for event in upcoming_events:
        confirmed_attendees = event.rsvps.filter(status='going').select_related('user')
        
        for rsvp in confirmed_attendees:
            subject = f"Reminder: {event.title} tomorrow!"
            message = f"Don't forget! {event.title} is tomorrow at {event.start_time.strftime('%I:%M %p')} at {event.location}."
            
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [rsvp.user.email])
```

## 🚀 **Performance Optimizations**

### **Database Optimizations**
```python
# Optimized RSVP queries with select_related and prefetch_related
rsvps = RSVP.objects.select_related(
    'user', 'event'
).prefetch_related(
    'event__category', 'event__tags'
).filter(event_id=event_id)

# Efficient counting with annotations
event_stats = Event.objects.annotate(
    going_count=Count('rsvps', filter=Q(rsvps__status='going')),
    waitlist_count=Count('rsvps', filter=Q(rsvps__status='waitlist')),
    total_rsvps=Count('rsvps')
).get(id=event_id)
```

### **Caching Strategy**
- **RSVP Counts**: Cache event RSVP statistics
- **User RSVPs**: Cache user RSVP history
- **Capacity Status**: Cache event full/available status

### **Background Processing**
- **Notifications**: Asynchronous email sending
- **Waitlist Processing**: Background waitlist management
- **Analytics**: Scheduled statistics computation

## 🧪 **Testing**

### **Test Structure**
```
tests/
├── test_models.py          # RSVP model tests
├── test_views.py           # View and endpoint tests
├── test_serializers.py     # Serializer tests
├── test_workflows.py       # RSVP workflow tests
├── test_capacity.py        # Capacity management tests
└── test_integration.py     # Integration tests
```

### **Running Tests**
```bash
# Test specific components
python manage.py test rsvp.test_models
python manage.py test rsvp.test_views
python manage.py test rsvp.test_workflows

# Test entire app
python manage.py test rsvp

# Test with coverage
coverage run --source='rsvp' manage.py test rsvp
coverage report
```

### **Test Examples**
```python
def test_rsvp_creation(self):
    """Test RSVP creation process."""
    event = Event.objects.create(
        title="Test Event",
        start_time=timezone.now() + timedelta(days=1),
        created_by=self.user
    )
    
    data = {'status': 'going'}
    response = self.client.post(f'/rsvp/events/{event.id}/rsvp/', data)
    
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertTrue(RSVP.objects.filter(user=self.user, event=event).exists())

def test_capacity_management(self):
    """Test event capacity management."""
    event = Event.objects.create(
        title="Limited Event",
        max_attendees=2,
        start_time=timezone.now() + timedelta(days=1),
        created_by=self.user
    )
    
    # Fill event to capacity
    user1 = User.objects.create_user('user1', 'user1@example.com', 'pass123')
    user2 = User.objects.create_user('user2', 'user2@example.com', 'pass123')
    
    RSVP.objects.create(user=user1, event=event, status='going')
    RSVP.objects.create(user=user2, event=event, status='going')
    
    # Third user should be waitlisted
    user3 = User.objects.create_user('user3', 'user3@example.com', 'pass123')
    rsvp3 = RSVP.objects.create(user=user3, event=event, status='going')
    
    self.assertEqual(rsvp3.status, 'waitlist')
```

## 🔧 **Configuration**

### **Settings Integration**
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'rsvp',
]

# RSVP settings
RSVP_SETTINGS = {
    'DEFAULT_STATUS': 'interested',
    'ALLOW_STATUS_CHANGES': True,
    'AUTO_WAITLIST': True,
    'REMINDER_DAYS': [1, 7],  # Send reminders 1 and 7 days before
}
```

### **URL Configuration**
```python
# Main app URLs
urlpatterns = [
    path('rsvp/', include('rsvp.urls')),
]
```

## 📚 **API Documentation**

### **RSVP Endpoints**

#### **Create/Update RSVP**
```bash
POST /rsvp/events/{event_id}/rsvp/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "status": "going",
    "notes": "Looking forward to it!"
}

# Response
{
    "id": 123,
    "user": 456,
    "event": 789,
    "status": "going",
    "notes": "Looking forward to it!",
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### **Get RSVP Status**
```bash
GET /rsvp/events/{event_id}/status/
Authorization: Bearer <jwt_token>

# Response
{
    "id": 123,
    "status": "going",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

#### **Get Event Attendees**
```bash
GET /rsvp/events/{event_id}/attendees/
Authorization: Bearer <jwt_token>

# Response
[
    {
        "user": {
            "id": 456,
            "username": "john_doe",
            "email": "john@example.com"
        },
        "status": "going",
        "rsvp_date": "2024-01-15T10:30:00Z"
    }
]
```

## 🚨 **Error Handling**

### **Common Error Responses**
```python
# Capacity Full Error
{
    "error": "Event is at full capacity. You have been added to the waitlist.",
    "status_code": 400,
    "rsvp_status": "waitlist"
}

# Duplicate RSVP Error
{
    "error": "You already have an RSVP for this event.",
    "status_code": 400,
    "existing_rsvp": {
        "id": 123,
        "status": "going"
    }
}

# Invalid Status Transition Error
{
    "error": "Invalid status transition from 'cancelled' to 'going'",
    "status_code": 400,
    "allowed_transitions": ["interested"]
}
```

### **Custom Exception Handling**
- **Capacity Errors**: Clear capacity and waitlist information
- **Validation Errors**: Field-level error messages
- **Business Logic Errors**: Contextual error information
- **Permission Errors**: Clear access control messages

## 🔮 **Future Enhancements**

### **Planned Features**
- **Group RSVPs**: RSVP for multiple people
- **RSVP Templates**: Predefined RSVP responses
- **Advanced Waitlist**: Priority-based waitlist management
- **RSVP Analytics**: Advanced reporting and insights

### **Integration Improvements**
- **Calendar Integration**: Add events to user calendars
- **Social Sharing**: Share RSVP status on social media
- **Mobile Notifications**: Push notifications for RSVP updates
- **Email Templates**: Rich HTML email notifications

### **Performance Enhancements**
- **Real-time Updates**: WebSocket support for live RSVP updates
- **Advanced Caching**: Redis-based caching for RSVP data
- **Background Processing**: Asynchronous RSVP processing
- **Database Optimization**: Advanced query optimization

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

**RSVP App** - The attendance management system for the Event Booking platform, providing robust RSVP handling, capacity management, and attendee analytics.
