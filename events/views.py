from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.db.models.functions import Extract
from django.utils import timezone
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Event, EventCategory, EventTag, Review
from .serializers import (
    EventSerializer, EventCreateSerializer, EventCategorySerializer,
    EventTagSerializer, ReviewSerializer, EventSearchSerializer
)
from .permissions import (
    IsOrganizerOrReadOnly, IsEventOwnerOrReadOnly, CanReviewEvent,
    IsAdminOrEventOwner, IsAdminOrOrganizerOrEventOwner
)

# Create your views here.

class EventCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing event categories.
    Public access for all users.
    """
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="List all event categories",
        operation_summary="List Event Categories",
        tags=['Public'],
        responses={
            200: openapi.Response('Success', EventCategorySerializer(many=True))
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get event category details",
        operation_summary="Get Event Category",
        tags=['Public'],
        responses={
            200: openapi.Response('Success', EventCategorySerializer),
            404: 'Category Not Found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class EventTagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing event tags.
    Public access for all users.
    """
    queryset = EventTag.objects.all()
    serializer_class = EventTagSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="List all event tags",
        operation_summary="List Event Tags",
        tags=['Public'],
        responses={
            200: openapi.Response('Success', EventTagSerializer(many=True))
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get event tag details",
        operation_summary="Get Event Tag",
        tags=['Public'],
        responses={
            200: openapi.Response('Success', EventTagSerializer),
            404: 'Tag Not Found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class EventViewSet(viewsets.ModelViewSet):
    """
    Main Event ViewSet with role-based access control.
    
    Access Levels:
    - Public: Read access to published events
    - Authenticated Users: Enhanced read access + RSVP operations
    - Organizers: Create events + manage their own events
    - Admins: Full access to all events
    """
    queryset = Event.objects.all()
    permission_classes = [AllowAny]  # Base permission, overridden in get_permissions
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'tags', 'is_recurring']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_time', 'title', 'created_at']
    ordering = ['-start_time']
    
    def get_permissions(self):
        """
        Dynamic permission assignment based on action and user role.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Write operations require authentication and appropriate permissions
            permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly, IsEventOwnerOrReadOnly]
        elif self.action in ['attendees', 'rsvp_status', 'stats']:
            # Enhanced read operations require authentication
            permission_classes = [IsAuthenticated]
        else:
            # Basic read operations are public
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer
    
    def get_queryset(self):
        """
        Role-based queryset filtering for enhanced data access.
        """
        # Fix for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Event.objects.none()
        
        # Base queryset with optimizations
        queryset = Event.objects.select_related('created_by', 'category').prefetch_related('tags', 'reviews')
        
        # Role-based data enhancement
        if self.request.user.is_authenticated:
            if self.request.user.is_staff or self.request.user.is_superuser:
                # Admin users get full access to all events
                pass
            elif self.request.user.is_organizer:
                # Organizers get enhanced data for their own events
                queryset = queryset.prefetch_related('rsvps')
            else:
                # Regular authenticated users get basic enhanced data
                queryset = queryset.prefetch_related('rsvps')
        
        return queryset

    @swagger_auto_schema(
        operation_description="List all events with filtering, search, and pagination",
        operation_summary="List Events",
        tags=['Public'],
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('tags', openapi.IN_QUERY, description="Filter by tag IDs (comma-separated)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in title, description, or location", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by: start_time, title, created_at", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('Success', EventSerializer(many=True)),
            400: 'Bad Request'
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get detailed information about a specific event",
        operation_summary="Get Event Details",
        tags=['Public'],
        responses={
            200: openapi.Response('Success', EventSerializer),
            404: 'Event Not Found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new event (Organizer role required)",
        operation_summary="Create Event",
        tags=['Events'],
        request_body=EventCreateSerializer,
        responses={
            201: openapi.Response('Event Created', EventSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden - Organizer role required'
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an existing event (Event owner or admin required)",
        operation_summary="Update Event",
        tags=['Events'],
        request_body=EventCreateSerializer,
        responses={
            200: openapi.Response('Event Updated', EventSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden - Event owner or admin required',
            404: 'Event Not Found'
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update an existing event (Event owner or admin required)",
        operation_summary="Partial Update Event",
        tags=['Events'],
        request_body=EventCreateSerializer,
        responses={
            200: openapi.Response('Event Updated', EventSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden - Event owner or admin required',
            404: 'Event Not Found'
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an event (Event owner or admin required)",
        operation_summary="Delete Event",
        tags=['Events'],
        responses={
            204: 'Event Deleted',
            401: 'Unauthorized',
            403: 'Forbidden - Event owner or admin required',
            404: 'Event Not Found'
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get list of attendees for an event with role-based access control",
        operation_summary="Get Event Attendees",
        tags=['Events'],
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, description="Event ID", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response('Success', EventSerializer),
            401: 'Unauthorized',
            404: 'Event Not Found'
        }
    )
    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """
        Get event attendees with role-based data access.
        - Public: No access
        - Authenticated: Basic attendee list (going status only)
        - Organizers/Admins: Full attendee list with details
        """
        # Fix for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Response([])
        
        event = self.get_object()
        
        # Role-based data access
        if request.user.is_staff or request.user.is_superuser:
            # Admin users get full attendee list
            attendees = event.rsvps.select_related('user').all()
        elif request.user.is_organizer and event.created_by == request.user:
            # Organizers get full attendee list for their events
            attendees = event.rsvps.select_related('user').all()
        else:
            # Regular users get basic attendee list (going status only)
            attendees = event.rsvps.filter(status='going').select_related('user')
        
        # Serialize attendee data
        attendee_data = []
        for rsvp in attendees:
            attendee_data.append({
                'user_id': rsvp.user.id,
                'username': rsvp.user.username,
                'status': rsvp.status,
                'rsvp_date': rsvp.created_at,
                'notes': rsvp.notes if request.user.is_staff or (request.user.is_organizer and event.created_by == request.user) else None
            })
        
        return Response({
            'event_id': event.id,
            'event_title': event.title,
            'total_attendees': len(attendee_data),
            'attendees': attendee_data
        })

    @swagger_auto_schema(
        operation_description="Get user's RSVP status for a specific event",
        operation_summary="Get RSVP Status",
        tags=['Events'],
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, description="Event ID", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response('Success', EventSerializer),
            401: 'Unauthorized',
            404: 'Event Not Found'
        }
    )
    @action(detail=True, methods=['get'])
    def rsvp_status(self, request, pk=None):
        """
        Get user's RSVP status for an event.
        Requires authentication.
        """
        # Fix for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Response({'status': 'not_rsvpd'})
        
        event = self.get_object()
        
        try:
            rsvp = event.rsvps.get(user=request.user)
            return Response({
                'event_id': event.id,
                'user_id': request.user.id,
                'status': rsvp.status,
                'rsvp_date': rsvp.created_at,
                'notes': rsvp.notes
            })
        except:
            return Response({'status': 'not_rsvpd'})

    @swagger_auto_schema(
        operation_description="Get event statistics with role-based data enhancement",
        operation_summary="Get Event Statistics",
        tags=['Events'],
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, description="Event ID", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response('Success', EventSerializer),
            401: 'Unauthorized',
            404: 'Event Not Found'
        }
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get event statistics with role-based data enhancement.
        - Public: No access
        - Authenticated: Basic statistics
        - Organizers/Admins: Enhanced statistics with analytics
        """
        # Fix for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Response({})
        
        event = self.get_object()
        
        # Basic statistics for all authenticated users
        basic_stats = {
            'total_rsvps': event.rsvps.count(),
            'going_count': event.rsvps.filter(status='going').count(),
            'interested_count': event.rsvps.filter(status='interested').count(),
            'cancelled_count': event.rsvps.filter(status='cancelled').count(),
            'available_spots': (event.max_attendees - event.rsvps.filter(status='going').count()) if event.max_attendees else None,
            'is_full': event.is_full,
            'average_rating': event.average_rating,
            'review_count': event.reviews.count()
        }
        
        # Enhanced statistics for organizers and admins
        if request.user.is_staff or request.user.is_superuser or (request.user.is_organizer and event.created_by == request.user):
            # RSVP timeline
            rsvp_timeline = event.rsvps.annotate(
                day=Extract('created_at', 'day')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            # Category performance
            category_performance = {
                'category_name': event.category.name if event.category else 'Uncategorized',
                'category_events_count': Event.objects.filter(category=event.category).count() if event.category else 0
            }
            
            enhanced_stats = {
                'rsvp_timeline': list(rsvp_timeline),
                'category_performance': category_performance,
                'capacity_utilization': (basic_stats['going_count'] / event.max_attendees * 100) if event.max_attendees else 0
            }
            
            basic_stats.update(enhanced_stats)
        
        return Response(basic_stats)

    @swagger_auto_schema(
        operation_description="Get enhanced event insights (Event owner, organizer, or admin required)",
        operation_summary="Get Event Insights",
        tags=['Events'],
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, description="Event ID", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response('Success', EventSerializer),
            401: 'Unauthorized',
            403: 'Forbidden - Event owner, organizer, or admin required',
            404: 'Event Not Found'
        }
    )
    @action(detail=True, methods=['get'])
    def insights(self, request, pk=None):
        """
        Get enhanced event insights for event owners, organizers, and admins.
        """
        # Fix for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Response({})
        
        event = self.get_object()
        
        # Check access permissions
        if not (request.user.is_staff or request.user.is_superuser or 
                (request.user.is_organizer and event.created_by == request.user)):
            return Response(
                {'error': 'Access denied. Only event owners, organizers, and admins can view insights.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Enhanced insights data
        insights = {
            'event_id': event.id,
            'event_title': event.title,
            'rsvp_breakdown': {
                'total': event.rsvps.count(),
                'going': event.rsvps.filter(status='going').count(),
                'interested': event.rsvps.filter(status='interested').count(),
                'waitlist': event.rsvps.filter(status='waitlist').count(),
                'cancelled': event.rsvps.filter(status='cancelled').count()
            },
            'engagement_metrics': {
                'rsvp_rate': (event.rsvps.count() / max(event.max_attendees, 1)) * 100 if event.max_attendees else 0,
                'conversion_rate': (event.rsvps.filter(status='going').count() / max(event.rsvps.count(), 1)) * 100,
                'average_rating': event.average_rating,
                'review_count': event.reviews.count()
            },
            'performance_analysis': {
                'days_until_event': (event.start_time - timezone.now()).days,
                'rsvp_trend': 'increasing' if event.rsvps.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7)).count() > event.rsvps.filter(created_at__gte=timezone.now() - timezone.timedelta(days=14), created_at__lt=timezone.now() - timezone.timedelta(days=7)).count() else 'decreasing',
                'capacity_utilization': (event.rsvps.filter(status='going').count() / max(event.max_attendees, 1)) * 100 if event.max_attendees else 0
            }
        }
        
        return Response(insights)

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating event reviews.
    Access: Authenticated users with event attendance verification
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, CanReviewEvent]
    
    def get_queryset(self):
        # Fix for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        
        event_id = self.kwargs.get('event_id')
        if event_id:
            return Review.objects.filter(event_id=event_id).select_related('user')
        return Review.objects.none()
    
    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_id')
        event = Event.objects.get(id=event_id)
        serializer.save(user=self.request.user, event=event)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['event_id'] = self.kwargs.get('event_id')
        return context
