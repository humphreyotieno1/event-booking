from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import requests
from .models import ExternalEvent
from .serializers import (
    ExternalEventSerializer, ExternalEventImportSerializer,
    ExternalEventSearchSerializer
)
from events.models import Event, EventCategory, EventTag
from events.serializers import EventSerializer

class ExternalEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing external events and integrating with external APIs.
    """
    queryset = ExternalEvent.objects.all()
    serializer_class = ExternalEventSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search external events from various providers."""
        serializer = ExternalEventSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        provider = data.get('provider', 'ticketmaster')
        
        if provider == 'ticketmaster':
            return self._search_ticketmaster(request, data)
        elif provider == 'seatgeek':
            return self._search_seatgeek(request, data)
        else:
            return Response(
                {'error': 'Unsupported provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _search_ticketmaster(self, request, data):
        """Search events from Ticketmaster API."""
        api_key = getattr(settings, 'TICKETMASTER_API_KEY', None)
        if not api_key:
            return Response(
                {'error': 'Ticketmaster API key not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Build API URL
        base_url = 'https://app.ticketmaster.com/discovery/v2/events.json'
        params = {
            'apikey': api_key,
            'size': 20,
        }
        
        if data.get('query'):
            params['keyword'] = data['query']
        if data.get('location'):
            params['city'] = data['location']
        if data.get('category'):
            params['classificationName'] = data['category']
        if data.get('date_from'):
            params['startDateTime'] = f"{data['date_from']}T00:00:00Z"
        if data.get('date_to'):
            params['endDateTime'] = f"{data['date_to']}T23:59:59Z"
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            events_data = response.json()
            
            # Process and return events
            events = []
            if 'events' in events_data and events_data['events']:
                for event_data in events_data['events']:
                    event = self._process_ticketmaster_event(event_data)
                    events.append(event)
            
            return Response({
                'events': events,
                'total': len(events),
                'provider': 'ticketmaster'
            })
            
        except requests.RequestException as e:
            return Response(
                {'error': f'Failed to fetch from Ticketmaster: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _search_seatgeek(self, request, data):
        """Search events from SeatGeek API."""
        # SeatGeek doesn't require an API key for basic searches
        base_url = 'https://api.seatgeek.com/2/events'
        params = {
            'per_page': 20,
        }
        
        if data.get('query'):
            params['q'] = data['query']
        if data.get('location'):
            params['venue.city'] = data['location']
        if data.get('category'):
            params['type'] = data['category']
        if data.get('date_from'):
            params['datetime_utc.gte'] = f"{data['date_from']}T00:00:00"
        if data.get('date_to'):
            params['datetime_utc.lte'] = f"{data['date_to']}T23:59:59"
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            events_data = response.json()
            
            # Process and return events
            events = []
            if 'events' in events_data and events_data['events']:
                for event_data in events_data['events']:
                    event = self._process_seatgeek_event(event_data)
                    events.append(event)
            
            return Response({
                'events': events,
                'total': len(events),
                'provider': 'seatgeek'
            })
            
        except requests.RequestException as e:
            return Response(
                {'error': f'Failed to fetch from SeatGeek: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_ticketmaster_event(self, event_data):
        """Process Ticketmaster event data into our format."""
        return {
            'external_id': event_data.get('id'),
            'provider': 'ticketmaster',
            'title': event_data.get('name'),
            'description': event_data.get('info', ''),
            'location': event_data.get('_embedded', {}).get('venues', [{}])[0].get('city', {}).get('name', ''),
            'start_time': event_data.get('dates', {}).get('start', {}).get('dateTime'),
            'venue_name': event_data.get('_embedded', {}).get('venues', [{}])[0].get('name', ''),
            'venue_address': event_data.get('_embedded', {}).get('venues', [{}])[0].get('address', {}).get('line1', ''),
            'image_url': event_data.get('images', [{}])[0].get('url', '') if event_data.get('images') else '',
            'ticket_url': event_data.get('url'),
            'price_range': event_data.get('priceRanges', [{}])[0].get('type', '') if event_data.get('priceRanges') else '',
            'category': event_data.get('classifications', [{}])[0].get('segment', {}).get('name', '') if event_data.get('classifications') else '',
            'tags': [c.get('name') for c in event_data.get('classifications', []) if c.get('name')],
            'raw_data': event_data
        }
    
    def _process_seatgeek_event(self, event_data):
        """Process SeatGeek event data into our format."""
        return {
            'external_id': str(event_data.get('id')),
            'provider': 'seatgeek',
            'title': event_data.get('title'),
            'description': event_data.get('description', ''),
            'location': event_data.get('venue', {}).get('city', ''),
            'start_time': event_data.get('datetime_utc'),
            'venue_name': event_data.get('venue', {}).get('name', ''),
            'venue_address': event_data.get('venue', {}).get('address', ''),
            'image_url': event_data.get('performers', [{}])[0].get('image', '') if event_data.get('performers') else '',
            'ticket_url': event_data.get('url'),
            'price_range': f"${event_data.get('stats', {}).get('lowest_price', 'N/A')} - ${event_data.get('stats', {}).get('highest_price', 'N/A')}" if event_data.get('stats') else '',
            'category': event_data.get('type', ''),
            'tags': [p.get('name') for p in event_data.get('performers', []) if p.get('name')],
            'raw_data': event_data
        }
    
    @action(detail=True, methods=['post'])
    def import_event(self, request, pk=None):
        """Import an external event into the local database."""
        external_event = self.get_object()
        
        if external_event.is_imported:
            return Response(
                {'error': 'Event already imported'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ExternalEventImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            # Create the local event
            event_data = {
                'title': external_event.title,
                'description': external_event.description,
                'location': external_event.location,
                'start_time': external_event.start_time,
                'end_time': external_event.end_time or external_event.start_time,
                'created_by': request.user,
                'external_event_id': external_event.external_id,
                'max_attendees': data.get('max_attendees'),
                'is_recurring': data.get('is_recurring', False),
                'recurrence_pattern': data.get('recurrence_pattern', ''),
            }
            
            # Set category if provided
            if data.get('category_id'):
                try:
                    category = EventCategory.objects.get(id=data['category_id'])
                    event_data['category'] = category
                except EventCategory.DoesNotExist:
                    pass
            
            # Create the event
            event = Event.objects.create(**event_data)
            
            # Add tags if provided
            if data.get('tag_ids'):
                tags = EventTag.objects.filter(id__in=data['tag_ids'])
                event.tags.set(tags)
            
            # Mark external event as imported
            external_event.is_imported = True
            external_event.imported_event = event
            external_event.save()
            
            return Response(
                EventSerializer(event).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': f'Failed to import event: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
