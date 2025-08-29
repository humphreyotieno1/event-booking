from rest_framework import permissions

class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow organizers to create events.
    """
    
    def has_permission(self, request, view):
        # Allow read operations for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only organizers can create events
        return request.user.is_authenticated and request.user.is_organizer

class IsEventOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow event owners to edit/delete their events.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow read operations for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only event owners can edit/delete
        return obj.created_by == request.user

class IsEventOwner(permissions.BasePermission):
    """
    Custom permission to only allow event owners to perform actions.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user

class CanReviewEvent(permissions.BasePermission):
    """
    Custom permission to only allow attendees to review events.
    """
    
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            # Check if user has RSVP'd to the event
            event_id = view.kwargs.get('event_id') or view.kwargs.get('pk')
            if event_id:
                from .models import Event
                try:
                    event = Event.objects.get(id=event_id)
                    # Only allow reviews for past events
                    if not event.is_past:
                        return False
                    # Check if user attended the event
                    return request.user.rsvps.filter(
                        event=event, 
                        status='going'
                    ).exists()
                except Event.DoesNotExist:
                    return False
        return True
