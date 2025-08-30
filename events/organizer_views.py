from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Sum, Min, Max
from django.db.models.functions import Extract
from django.utils import timezone
from datetime import datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Event, EventCategory, EventTag, Review
from .serializers import (
    EventSerializer, EventCreateSerializer, EventCategorySerializer,
    EventTagSerializer, ReviewSerializer
)
from .permissions import IsOrganizer, IsAdminOrOrganizer
from rsvp.models import RSVP


class OrganizerEventViewSet(viewsets.ModelViewSet):
    """
    Organizer-specific ViewSet for managing their own events with enhanced analytics.
    Provides detailed insights for event organizers.
    """
    serializer_class = EventSerializer
    permission_classes = [IsOrganizer]
    filter_backends = []
    
    def get_queryset(self):
        """
        Organizers can only see their own events with enhanced data.
        """
        return Event.objects.filter(
            created_by=self.request.user
        ).select_related(
            'created_by', 'category'
        ).prefetch_related(
            'tags', 'reviews', 'rsvps'
        ).all()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer

    @swagger_auto_schema(
        operation_description="List organizer's own events with enhanced data",
        operation_summary="List Organizer Events",
        tags=['Organizer'],
        responses={
            200: openapi.Response('Success', EventSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden - Organizer role required'
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get detailed information about organizer's own event",
        operation_summary="Get Organizer Event Details",
        tags=['Organizer'],
        responses={
            200: openapi.Response('Success', EventSerializer),
            401: 'Unauthorized',
            403: 'Forbidden - Organizer role required',
            404: 'Event Not Found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new event (Organizer role required)",
        operation_summary="Create Event",
        tags=['Organizer'],
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
        operation_description="Update organizer's own event",
        operation_summary="Update Event",
        tags=['Organizer'],
        request_body=EventCreateSerializer,
        responses={
            200: openapi.Response('Event Updated', EventSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden - Organizer role required',
            404: 'Event Not Found'
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update organizer's own event",
        operation_summary="Partial Update Event",
        tags=['Organizer'],
        request_body=EventCreateSerializer,
        responses={
            200: openapi.Response('Event Updated', EventSerializer),
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden - Organizer role required',
            404: 'Event Not Found'
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete organizer's own event",
        operation_summary="Delete Event",
        tags=['Organizer'],
        responses={
            204: 'Event Deleted',
            401: 'Unauthorized',
            403: 'Forbidden - Organizer role required',
            404: 'Event Not Found'
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Get organizer-specific dashboard with event performance metrics",
        operation_summary="Organizer Dashboard",
        tags=['Organizer'],
        responses={
            200: openapi.Response('Success', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_events': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total events created by organizer'),
                    'upcoming_events': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of upcoming events'),
                    'past_events': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of past events'),
                    'events_this_month': openapi.Schema(type=openapi.TYPE_INTEGER, description='Events created this month'),
                    'total_rsvps': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total RSVPs across all organizer events'),
                    'rsvps_this_month': openapi.Schema(type=openapi.TYPE_INTEGER, description='RSVPs created this month'),
                    'top_performing_events': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'category_performance': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )),
            401: 'Unauthorized',
            403: 'Forbidden - Organizer role required'
        }
    )
    @action(detail=False, methods=['get'])
    def organizer_dashboard(self, request):
        """
        Get organizer-specific dashboard with event performance metrics.
        """
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Organizer's event statistics
        user_events = Event.objects.filter(created_by=request.user)
        total_events = user_events.count()
        upcoming_events = user_events.filter(start_time__gte=now).count()
        past_events = user_events.filter(start_time__lt=now).count()
        events_this_month = user_events.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # RSVP statistics for organizer's events
        total_rsvps = RSVP.objects.filter(event__created_by=request.user).count()
        rsvps_this_month = RSVP.objects.filter(
            event__created_by=request.user,
            created_at__gte=thirty_days_ago
        ).count()
        
        # Event performance metrics
        event_performance = user_events.annotate(
            rsvp_count=Count('rsvps'),
            going_count=Count('rsvps', filter=Q(rsvps__status='going')),
            interested_count=Count('rsvps', filter=Q(rsvps__status='interested')),
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        ).values(
            'id', 'title', 'start_time', 'rsvp_count', 'going_count',
            'interested_count', 'review_count', 'avg_rating'
        ).order_by('-rsvp_count')[:10]
        
        # Category performance for organizer
        category_performance = EventCategory.objects.filter(
            events__created_by=request.user
        ).annotate(
            event_count=Count('events'),
            total_rsvps=Count('events__rsvps'),
            avg_rating=Avg('events__reviews__rating')
        ).values('name', 'event_count', 'total_rsvps', 'avg_rating')
        
        dashboard_data = {
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'past_events': past_events,
            'events_this_month': events_this_month,
            'total_rsvps': total_rsvps,
            'rsvps_this_month': rsvps_this_month,
            'top_performing_events': list(event_performance),
            'category_performance': list(category_performance)
        }
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'])
    def event_analytics(self, request):
        """
        Get detailed analytics for organizer's events.
        """
        user_events = Event.objects.filter(created_by=request.user)
        
        # Event engagement metrics
        engagement_metrics = user_events.annotate(
            rsvp_count=Count('rsvps'),
            going_count=Count('rsvps', filter=Q(rsvps__status='going')),
            interested_count=Count('rsvps', filter=Q(rsvps__status='interested')),
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        ).values(
            'id', 'title', 'start_time', 'rsvp_count', 'going_count',
            'interested_count', 'review_count', 'avg_rating'
        ).order_by('-rsvp_count')
        
        # Time-based trends for organizer
        monthly_trends = user_events.filter(
            created_at__gte=timezone.now() - timedelta(days=365)
        ).annotate(
            month=Extract('created_at', 'month')
        ).values('month').annotate(
            event_count=Count('id'),
            avg_rsvps=Avg('rsvps__count')
        ).order_by('month')
        
        # Audience insights
        audience_insights = user_events.aggregate(
            total_unique_attendees=Count('rsvps__user', distinct=True),
            avg_rsvps_per_event=Avg('rsvps__count'),
            total_reviews=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        )
        
        analytics = {
            'engagement_metrics': list(engagement_metrics),
            'monthly_trends': list(monthly_trends),
            'audience_insights': audience_insights
        }
        
        return Response(analytics)
    
    @action(detail=True, methods=['get'])
    def event_insights(self, request, pk=None):
        """
        Get detailed insights for a specific event owned by the organizer.
        """
        event = self.get_object()
        
        # Verify ownership
        if event.created_by != request.user:
            return Response(
                {'error': 'You can only view insights for your own events'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # RSVP breakdown
        rsvp_breakdown = event.rsvps.values('status').annotate(
            count=Count('id')
        )
        
        # Attendee demographics
        attendee_demographics = event.rsvps.filter(
            status='going'
        ).values('user__username').annotate(
            rsvp_count=Count('id')
        ).order_by('-rsvp_count')[:20]
        
        # Review analysis
        review_analysis = event.reviews.aggregate(
            total_reviews=Count('id'),
            avg_rating=Avg('rating'),
            min_rating=Min('rating'),
            max_rating=Max('rating')
        )
        
        # Engagement timeline
        engagement_timeline = event.rsvps.extra(
            select={'day': "EXTRACT(day FROM created_at)"}
        ).values('day').annotate(
            rsvp_count=Count('id')
        ).order_by('day')
        
        insights = {
            'event_info': {
                'id': event.id,
                'title': event.title,
                'start_time': event.start_time,
                'category': event.category.name if event.category else None
            },
            'rsvp_breakdown': list(rsvp_breakdown),
            'attendee_demographics': list(attendee_demographics),
            'review_analysis': review_analysis,
            'engagement_timeline': list(engagement_timeline),
            'total_rsvps': event.rsvps.count(),
            'available_spots': event.available_spots,
            'is_full': event.is_full
        }
        
        return Response(insights)
    
    @action(detail=True, methods=['get'])
    def attendee_list(self, request, pk=None):
        """
        Get detailed attendee list for organizer's event.
        """
        event = self.get_object()
        
        # Verify ownership
        if event.created_by != request.user:
            return Response(
                {'error': 'You can only view attendees for your own events'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all RSVPs with user details
        rsvps = event.rsvps.select_related('user').all()
        
        attendee_data = []
        for rsvp in rsvps:
            attendee_data.append({
                'user_id': rsvp.user.id,
                'username': rsvp.user.username,
                'email': rsvp.user.email,
                'status': rsvp.status,
                'rsvp_date': rsvp.created_at,
                'is_verified': rsvp.user.email_verified
            })
        
        return Response({
            'event_title': event.title,
            'total_attendees': len(attendee_data),
            'attendees': attendee_data
        })
    
    @action(detail=False, methods=['get'])
    def upcoming_events(self, request):
        """
        Get organizer's upcoming events with RSVP counts.
        """
        upcoming_events = Event.objects.filter(
            created_by=request.user,
            start_time__gte=timezone.now()
        ).annotate(
            rsvp_count=Count('rsvps'),
            going_count=Count('rsvps', filter=Q(rsvps__status='going'))
        ).values(
            'id', 'title', 'start_time', 'location', 'rsvp_count', 'going_count'
        ).order_by('start_time')
        
        return Response(list(upcoming_events))
    
    @action(detail=False, methods=['get'])
    def past_events(self, request):
        """
        Get organizer's past events with performance metrics.
        """
        past_events = Event.objects.filter(
            created_by=request.user,
            start_time__lt=timezone.now()
        ).annotate(
            rsvp_count=Count('rsvps'),
            going_count=Count('rsvps', filter=Q(rsvps__status='going')),
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        ).values(
            'id', 'title', 'start_time', 'location', 'rsvp_count', 
            'going_count', 'review_count', 'avg_rating'
        ).order_by('-start_time')
        
        return Response(list(past_events))
