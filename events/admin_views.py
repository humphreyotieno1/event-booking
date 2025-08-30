from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Event, EventCategory, EventTag, Review
from .serializers import (
    EventSerializer, EventCreateSerializer, EventCategorySerializer,
    EventTagSerializer, ReviewSerializer
)
from .permissions import IsAdminUser, IsAdminOrOrganizer
from rsvp.models import RSVP


class AdminEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin-only ViewSet for comprehensive event management and analytics.
    Provides enhanced data access for administrative purposes.
    """
    serializer_class = EventSerializer
    permission_classes = [IsAdminUser]
    filter_backends = []
    
    def get_queryset(self):
        """
        Admin users can see all events with enhanced data.
        """
        return Event.objects.select_related(
            'created_by', 'category'
        ).prefetch_related(
            'tags', 'reviews', 'rsvps'
        ).all()

    @swagger_auto_schema(
        operation_description="List all events with admin-level access and enhanced data",
        operation_summary="List All Events (Admin)",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', EventSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required'
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get detailed event information with admin-level access",
        operation_summary="Get Event Details (Admin)",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', EventSerializer),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required',
            404: 'Event Not Found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Get comprehensive dashboard statistics for admin users",
        operation_summary="Admin Dashboard Statistics",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_events': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of events'),
                    'upcoming_events': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of upcoming events'),
                    'past_events': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of past events'),
                    'events_this_month': openapi.Schema(type=openapi.TYPE_INTEGER, description='Events created this month'),
                    'total_rsvps': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total RSVPs across all events'),
                    'rsvps_this_month': openapi.Schema(type=openapi.TYPE_INTEGER, description='RSVPs created this month'),
                    'active_organizers': openapi.Schema(type=openapi.TYPE_INTEGER, description='Active organizers this month'),
                    'category_distribution': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'recent_events': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'recent_rsvps': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required'
        }
    )
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Get comprehensive dashboard statistics for admin users.
        """
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Event statistics
        total_events = Event.objects.count()
        upcoming_events = Event.objects.filter(start_time__gte=now).count()
        past_events = Event.objects.filter(start_time__lt=now).count()
        events_this_month = Event.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # RSVP statistics
        total_rsvps = RSVP.objects.count()
        rsvps_this_month = RSVP.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # User engagement
        active_organizers = Event.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('created_by').distinct().count()
        
        # Category distribution
        category_stats = EventCategory.objects.annotate(
            event_count=Count('events')
        ).values('name', 'event_count')
        
        # Recent activity
        recent_events = Event.objects.filter(
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')[:10]
        
        recent_rsvps = RSVP.objects.filter(
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')[:10]
        
        stats = {
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'past_events': past_events,
            'events_this_month': events_this_month,
            'total_rsvps': total_rsvps,
            'rsvps_this_month': rsvps_this_month,
            'active_organizers': active_organizers,
            'category_distribution': list(category_stats),
            'recent_events': EventSerializer(recent_events, many=True).data,
            'recent_rsvps': [
                {
                    'id': rsvp.id,
                    'user': rsvp.user.username,
                    'event': rsvp.event.title,
                    'status': rsvp.status,
                    'created_at': rsvp.created_at
                }
                for rsvp in recent_rsvps
            ]
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def user_analytics(self, request):
        """
        Get user analytics and behavior patterns.
        """
        from accounts.models import User
        
        # User statistics
        total_users = User.objects.count()
        organizers = User.objects.filter(is_organizer=True).count()
        verified_users = User.objects.filter(email_verified=True).count()
        
        # User engagement
        active_users = User.objects.filter(
            rsvps__created_at__gte=timezone.now() - timedelta(days=30)
        ).distinct().count()
        
        # Top organizers
        top_organizers = User.objects.filter(is_organizer=True).annotate(
            event_count=Count('events'),
            total_rsvps=Sum('events__rsvps__count')
        ).order_by('-event_count')[:10]
        
        analytics = {
            'total_users': total_users,
            'organizers': organizers,
            'verified_users': verified_users,
            'active_users': active_users,
            'top_organizers': [
                {
                    'username': user.username,
                    'email': user.email,
                    'event_count': user.event_count or 0,
                    'total_rsvps': user.total_rsvps or 0
                }
                for user in top_organizers
            ]
        }
        
        return Response(analytics)
    
    @action(detail=False, methods=['get'])
    def event_analytics(self, request):
        """
        Get detailed event analytics and performance metrics.
        """
        # Event performance metrics
        event_performance = Event.objects.annotate(
            rsvp_count=Count('rsvps'),
            going_count=Count('rsvps', filter=Q(rsvps__status='going')),
            interested_count=Count('rsvps', filter=Q(rsvps__status='interested')),
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        ).values(
            'id', 'title', 'start_time', 'rsvp_count', 'going_count',
            'interested_count', 'review_count', 'avg_rating'
        ).order_by('-rsvp_count')[:20]
        
        # Category performance
        category_performance = EventCategory.objects.annotate(
            event_count=Count('events'),
            total_rsvps=Sum('events__rsvps__count'),
            avg_rating=Avg('events__reviews__rating')
        ).values('name', 'event_count', 'total_rsvps', 'avg_rating')
        
        # Time-based trends
        monthly_trends = Event.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=365)
        ).extra(
            select={'month': "EXTRACT(month FROM created_at)"}
        ).values('month').annotate(
            event_count=Count('id'),
            avg_rsvps=Avg('rsvps__count')
        ).order_by('month')
        
        analytics = {
            'top_performing_events': list(event_performance),
            'category_performance': list(category_performance),
            'monthly_trends': list(monthly_trends)
        }
        
        return Response(analytics)
    
    @action(detail=True, methods=['get'])
    def detailed_stats(self, request, pk=None):
        """
        Get detailed statistics for a specific event (admin view).
        """
        event = self.get_object()
        
        # RSVP breakdown
        rsvp_breakdown = event.rsvps.values('status').annotate(
            count=Count('id')
        )
        
        # User demographics (if available)
        user_demographics = event.rsvps.values('user__username').annotate(
            rsvp_count=Count('id')
        ).order_by('-rsvp_count')[:20]
        
        # Review analysis
        review_analysis = event.reviews.aggregate(
            total_reviews=Count('id'),
            avg_rating=Avg('rating'),
            min_rating=Min('rating'),
            max_rating=Max('rating')
        )
        
        detailed_stats = {
            'event_info': {
                'id': event.id,
                'title': event.title,
                'start_time': event.start_time,
                'created_by': event.created_by.username,
                'category': event.category.name if event.category else None
            },
            'rsvp_breakdown': list(rsvp_breakdown),
            'user_demographics': list(user_demographics),
            'review_analysis': review_analysis,
            'total_rsvps': event.rsvps.count(),
            'available_spots': event.available_spots,
            'is_full': event.is_full
        }
        
        return Response(detailed_stats)


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing event categories with enhanced operations.
    """
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """
        Debug authentication issues.
        """
        # Fix for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return EventCategory.objects.none()
        
        # Debug authentication
        if not self.request.user.is_authenticated:
            print(f"DEBUG: User not authenticated. Request user: {self.request.user}")
            print(f"DEBUG: Request headers: {dict(self.request.headers)}")
        else:
            print(f"DEBUG: User authenticated: {self.request.user.username}")
            print(f"DEBUG: User is_staff: {self.request.user.is_staff}")
            print(f"DEBUG: User is_superuser: {self.request.user.is_superuser}")
        
        return EventCategory.objects.all()

    @swagger_auto_schema(
        operation_description="List all event categories with admin-level access",
        operation_summary="List Event Categories (Admin)",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', EventCategorySerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required'
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get event category details with admin-level access",
        operation_summary="Get Event Category (Admin)",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', EventCategorySerializer),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required',
            404: 'Category Not Found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Get category usage statistics for admin users",
        operation_summary="Category Usage Statistics",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT)
            )),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required'
        }
    )
    @action(detail=False, methods=['get'])
    def usage_stats(self, request):
        """
        Get category usage statistics for admin users.
        """
        category_stats = EventCategory.objects.annotate(
            event_count=Count('events'),
            total_rsvps=Sum('events__rsvps__count'),
            avg_rating=Avg('events__reviews__rating')
        ).values('name', 'event_count', 'total_rsvps', 'avg_rating')
        
        return Response(list(category_stats))


class AdminTagViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing event tags with enhanced operations.
    """
    queryset = EventTag.objects.all()
    serializer_class = EventTagSerializer
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="List all event tags with admin-level access",
        operation_summary="List Event Tags (Admin)",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', EventTagSerializer(many=True)),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required'
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get event tag details with admin-level access",
        operation_summary="Get Event Tag (Admin)",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', EventTagSerializer),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required',
            404: 'Tag Not Found'
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Get tag usage statistics for admin users",
        operation_summary="Tag Usage Statistics",
        tags=['Admin'],
        responses={
            200: openapi.Response('Success', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT)
            )),
            401: 'Unauthorized',
            403: 'Forbidden - Admin privileges required'
        }
    )
    @action(detail=False, methods=['get'])
    def usage_stats(self, request):
        """
        Get tag usage statistics for admin users.
        """
        tag_stats = EventTag.objects.annotate(
            event_count=Count('events'),
            total_rsvps=Sum('events__rsvps__count')
        ).values('name', 'event_count', 'total_rsvps')
        
        return Response(list(tag_stats))
