# Event Booking System - Access Control Guide

## Overview

This document outlines the comprehensive access control system implemented for the Event Booking application, following Django REST framework best practices and security standards.

## User Roles and Permissions

### 1. Public Users (Unauthenticated)
**Access Level**: Basic read-only access
**Permissions**: None required

**Available Endpoints**:
- `GET /events/` - List all events (basic information)
- `GET /events/{id}/` - View event details
- `GET /categories/` - List event categories
- `GET /tags/` - List event tags

**Data Access**: Limited to public event information only

### 2. Authenticated Users
**Access Level**: Enhanced read access + personal operations
**Permissions**: `IsAuthenticated`

**Available Endpoints**:
- All public endpoints
- `GET /events/{id}/attendees/` - View event attendees (limited data)
- `GET /events/{id}/rsvp_status/` - Check personal RSVP status
- `GET /events/{id}/stats/` - View event statistics (basic)
- `POST /reviews/` - Create event reviews
- `GET /reviews/` - List event reviews

**Data Access**: Basic event data + personal RSVP information

### 3. Organizers
**Access Level**: Event management + enhanced analytics
**Permissions**: `IsOrganizer` + `IsEventOwnerOrReadOnly`

**Available Endpoints**:
- All authenticated user endpoints
- `POST /events/` - Create new events
- `PUT/PATCH /events/{id}/` - Update own events
- `DELETE /events/{id}/` - Delete own events
- `GET /organizer/events/` - List own events
- `GET /organizer/events/organizer_dashboard/` - Organizer dashboard
- `GET /organizer/events/event_analytics/` - Event analytics
- `GET /organizer/events/{id}/event_insights/` - Event insights
- `GET /organizer/events/{id}/attendee_list/` - Detailed attendee list
- `GET /organizer/events/upcoming_events/` - Upcoming events
- `GET /organizer/events/past_events/` - Past events

**Data Access**: Enhanced data for own events + comprehensive analytics

### 4. Administrators (Staff/Superuser)
**Access Level**: Full system access + comprehensive analytics
**Permissions**: `IsAdminUser` + `IsAdminOrEventOwner`

**Available Endpoints**:
- All organizer endpoints
- `GET /admin/events/` - List all events (admin view)
- `GET /admin/events/dashboard_stats/` - Admin dashboard statistics
- `GET /admin/events/user_analytics/` - User analytics
- `GET /admin/events/event_analytics/` - Event analytics
- `GET /admin/events/{id}/detailed_stats/` - Detailed event statistics
- `GET /admin/categories/` - Manage categories
- `GET /admin/categories/usage_stats/` - Category usage statistics
- `GET /admin/tags/` - Manage tags
- `GET /admin/tags/usage_stats/` - Tag usage statistics

**Data Access**: Full access to all data + system-wide analytics

## Permission Classes

### Core Permission Classes

```python
class IsOrganizerOrReadOnly(permissions.BasePermission):
    """Allows organizers to create events, others read-only access"""
    
class IsEventOwnerOrReadOnly(permissions.BasePermission):
    """Allows event owners to edit/delete their events"""
    
class IsAdminUser(permissions.BasePermission):
    """Restricts access to admin users (staff/superuser)"""
    
class IsOrganizer(permissions.BasePermission):
    """Restricts access to organizer users only"""
    
class IsAdminOrOrganizer(permissions.BasePermission):
    """Allows both admin users and organizers"""
    
class IsAdminOrEventOwner(permissions.BasePermission):
    """Allows admin users or event owners"""
    
class IsAdminOrOrganizerOrEventOwner(permissions.BasePermission):
    """Allows admin users, organizers, or event owners"""
```

### Permission Assignment Strategy

1. **Public Endpoints**: No permission classes required
2. **Authenticated Endpoints**: `IsAuthenticated` only
3. **Organizer Endpoints**: `IsOrganizer` + ownership verification
4. **Admin Endpoints**: `IsAdminUser` for full access
5. **Mixed Access**: Combined permissions for flexible access control

## Data Access Patterns

### 1. Role-Based Queryset Filtering

```python
def get_queryset(self):
    queryset = Event.objects.select_related('created_by', 'category')
    
    if self.request.user.is_authenticated:
        if self.request.user.is_staff or self.request.user.is_superuser:
            # Admin users get full access
            pass
        elif self.request.user.is_organizer:
            # Organizers get enhanced data for their events
            queryset = queryset.prefetch_related('rsvps')
        else:
            # Regular users get basic enhanced data
            queryset = queryset.prefetch_related('rsvps')
    
    return queryset
```

### 2. Action-Based Permission Assignment

```python
def get_permissions(self):
    if self.action in ['create', 'update', 'partial_update', 'destroy']:
        permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly, IsEventOwnerOrReadOnly]
    elif self.action in ['attendees', 'rsvp_status', 'stats']:
        permission_classes = [IsAuthenticated]
    else:
        permission_classes = [AllowAny]
    return [permission() for permission in permission_classes]
```

### 3. Conditional Data Enhancement

```python
# Enhanced statistics for organizers and admins
if request.user.is_staff or request.user.is_superuser or (
    request.user.is_organizer and event.created_by == request.user
):
    stats.update({
        'rsvp_timeline': list(event.rsvps.extra(...)),
        'category_performance': {...}
    })
```

## Security Best Practices

### 1. Authentication Requirements
- All write operations require authentication
- Sensitive data access requires appropriate role verification
- Session-based authentication with proper timeout handling

### 2. Authorization Checks
- Object-level permissions for event ownership
- Role-based access control for system-wide operations
- Proper validation of user claims and permissions

### 3. Data Exposure Control
- Public endpoints expose minimal data
- Enhanced data only available to authorized users
- Personal information protected by ownership verification

### 4. Input Validation
- Serializer validation for all input data
- Permission checks before data access
- Proper error handling and status codes

## API Endpoint Organization

### URL Structure
```
/events/                    # Public event endpoints
/events/{id}/attendees/     # Authenticated user endpoints
/events/{id}/stats/         # Role-based data access
/organizer/events/          # Organizer-specific endpoints
/admin/events/              # Admin-only endpoints
```

### Response Format Standardization
- Consistent error response format
- Role-appropriate data inclusion
- Proper HTTP status codes
- Pagination for list endpoints

## Testing and Validation

### Permission Testing
- Test all permission combinations
- Verify role-based access control
- Validate object-level permissions
- Test unauthorized access attempts

### Data Access Testing
- Verify data filtering by role
- Test enhanced data availability
- Validate ownership restrictions
- Test cross-user data isolation

## Monitoring and Logging

### Access Logging
- Log all permission checks
- Track failed access attempts
- Monitor role-based data access
- Audit admin operations

### Performance Monitoring
- Monitor query performance by role
- Track data access patterns
- Optimize permission checks
- Monitor memory usage for large datasets

## Future Enhancements

### 1. Advanced Role Management
- Custom role definitions
- Role hierarchy implementation
- Dynamic permission assignment
- Role-based feature flags

### 2. Enhanced Analytics
- Real-time permission analytics
- Access pattern analysis
- Security event monitoring
- Performance optimization insights

### 3. API Rate Limiting
- Role-based rate limiting
- Endpoint-specific limits
- User behavior monitoring
- Abuse prevention measures

## Conclusion

This access control system provides a robust, scalable foundation for the Event Booking application while maintaining security best practices and user experience standards. The role-based approach ensures appropriate data access while enabling powerful analytics and management capabilities for different user types.
