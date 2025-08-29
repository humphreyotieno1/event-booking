from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import RSVP
from .serializers import (
    RSVPSerializer, RSVPCreateSerializer, AttendeeSerializer
)
from .permissions import CanRSVPToEvent, CanViewAttendees, IsRSVPOwnerOrReadOnly
from events.models import Event

class RSVPViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing RSVPs.
    """
    serializer_class = RSVPSerializer
    permission_classes = [IsAuthenticated, CanRSVPToEvent, IsRSVPOwnerOrReadOnly]
    
    def get_queryset(self):
        return RSVP.objects.filter(user=self.request.user).select_related('event', 'user')
    
    @action(detail=False, methods=['post'], url_path='events/(?P<event_id>[^/.]+)')
    def rsvp_to_event(self, request, event_id=None):
        """RSVP to a specific event."""
        event = get_object_or_404(Event, id=event_id)
        user = request.user
        
        # Check if event is full
        if event.is_full:
            return Response(
                {'error': 'This event is already at full capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if event is in the past
        if event.is_past:
            return Response(
                {'error': 'Cannot RSVP to past events.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RSVPCreateSerializer(
            data=request.data,
            context={'request': request, 'event_id': event_id}
        )
        
        if serializer.is_valid():
            rsvp = serializer.save()
            return Response(
                RSVPSerializer(rsvp).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='events/(?P<event_id>[^/.]+)/cancel')
    def cancel_rsvp(self, request, event_id=None):
        """Cancel RSVP to a specific event."""
        event = get_object_or_404(Event, id=event_id)
        user = request.user
        
        try:
            rsvp = RSVP.objects.get(user=user, event=event)
            rsvp.status = 'cancelled'
            rsvp.save()
            return Response(
                RSVPSerializer(rsvp).data,
                status=status.HTTP_200_OK
            )
        except RSVP.DoesNotExist:
            return Response(
                {'error': 'No RSVP found for this event.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='events/(?P<event_id>[^/.]+)/attendees')
    def event_attendees(self, request, event_id=None):
        """Get list of attendees for a specific event."""
        event = get_object_or_404(Event, id=event_id)
        attendees = event.rsvps.filter(status='going').select_related('user')
        
        serializer = AttendeeSerializer(attendees, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-events')
    def my_events(self, request):
        """Get events that the current user has RSVP'd to."""
        user = request.user
        rsvps = RSVP.objects.filter(
            user=user,
            status='going'
        ).select_related('event').order_by('event__start_time')
        
        serializer = RSVPSerializer(rsvps, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-rsvps')
    def my_rsvps(self, request):
        """Get all RSVPs for the current user."""
        user = request.user
        rsvps = RSVP.objects.filter(user=user).select_related('event').order_by('-created_at')
        
        serializer = RSVPSerializer(rsvps, many=True)
        return Response(serializer.data)
