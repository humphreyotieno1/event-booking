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

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users (staff or superuser).
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )

class IsOrganizer(permissions.BasePermission):
    """
    Custom permission to only allow organizer users.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_organizer

class IsAdminOrOrganizer(permissions.BasePermission):
    """
    Custom permission to allow both admin users and organizers.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.is_superuser or 
            request.user.is_organizer
        )

class IsAdminOrEventOwner(permissions.BasePermission):
    """
    Custom permission to allow admin users or event owners.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Event owners can access their own events
        return obj.created_by == request.user

class IsAdminOrOrganizerOrEventOwner(permissions.BasePermission):
    """
    Custom permission to allow admin users, organizers, or event owners.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Organizers can access events they created
        if request.user.is_organizer and obj.created_by == request.user:
            return True
        
        # Event owners can access their own events
        return obj.created_by == request.user
