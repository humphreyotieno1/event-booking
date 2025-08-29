from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from .models import Event, EventCategory, EventTag, Review
from .serializers import (
    EventSerializer, EventCreateSerializer, EventCategorySerializer,
    EventTagSerializer, ReviewSerializer, EventSearchSerializer
)
from .permissions import (
    IsOrganizerOrReadOnly, IsEventOwnerOrReadOnly, CanReviewEvent
)

# Create your views here.

class EventCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing event categories.
    """
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [IsAuthenticated]

class EventTagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing event tags.
    """
    queryset = EventTag.objects.all()
    serializer_class = EventTagSerializer
    permission_classes = [IsAuthenticated]

class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating events.
    """
    queryset = Event.objects.all()
    permission_classes = [IsOrganizerOrReadOnly, IsEventOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'tags', 'is_recurring']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_time', 'title', 'created_at']
    ordering = ['-start_time']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer
    
    def get_queryset(self):
        queryset = Event.objects.select_related('created_by', 'category').prefetch_related('tags', 'reviews')
        
        # Apply search filters
        search_serializer = EventSearchSerializer(data=self.request.query_params)
        if search_serializer.is_valid():
            data = search_serializer.validated_data
            
            # Text search
            if data.get('q'):
                query = data['q']
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(location__icontains=query)
                )
            
            # Date range filter
            if data.get('date_from'):
                queryset = queryset.filter(start_time__date__gte=data['date_from'])
            if data.get('date_to'):
                queryset = queryset.filter(start_time__date__lte=data['date_to'])
            
            # Location filter
            if data.get('location'):
                queryset = queryset.filter(location__icontains=data['location'])
            
            # Organizer filter
            if data.get('organizer_id'):
                queryset = queryset.filter(created_by_id=data['organizer_id'])
            
            # Tag filter
            if data.get('tag_ids'):
                queryset = queryset.filter(tags__id__in=data['tag_ids'])
            
            # Sort by popularity (based on RSVP count)
            if data.get('sort_by') == 'popularity':
                queryset = queryset.annotate(
                    rsvp_count=Count('rsvps', filter=Q(rsvps__status='going'))
                )
                if data.get('sort_order') == 'asc':
                    queryset = queryset.order_by('rsvp_count')
                else:
                    queryset = queryset.order_by('-rsvp_count')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """Get list of attendees for a specific event."""
        event = self.get_object()
        attendees = event.rsvps.filter(status='going').select_related('user')
        
        from rsvp.serializers import AttendeeSerializer
        serializer = AttendeeSerializer(attendees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rsvp_status(self, request, pk=None):
        """Get current user's RSVP status for this event."""
        event = self.get_object()
        user = request.user
        
        try:
            rsvp = event.rsvps.get(user=user)
            from rsvp.serializers import RSVPSerializer
            serializer = RSVPSerializer(rsvp)
            return Response(serializer.data)
        except:
            return Response({'status': 'not_rsvpd'})
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get event statistics."""
        event = self.get_object()
        
        stats = {
            'total_rsvps': event.rsvps.count(),
            'going_count': event.rsvps.filter(status='going').count(),
            'interested_count': event.rsvps.filter(status='interested').count(),
            'cancelled_count': event.rsvps.filter(status='cancelled').count(),
            'available_spots': event.available_spots,
            'is_full': event.is_full,
            'average_rating': event.average_rating,
            'review_count': event.reviews.count(),
        }
        
        return Response(stats)

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating event reviews.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, CanReviewEvent]
    
    def get_queryset(self):
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
