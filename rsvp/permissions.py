from rest_framework import permissions

class CanRSVPToEvent(permissions.BasePermission):
    """
    Custom permission to only allow authenticated users to RSVP to events.
    """
    
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return True

class CanViewAttendees(permissions.BasePermission):
    """
    Custom permission to only allow authenticated users to view attendee lists.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated

class IsRSVPOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow RSVP owners to modify their RSVPs.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow read operations for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only RSVP owners can modify
        return obj.user == request.user
