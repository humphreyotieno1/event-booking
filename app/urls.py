from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import HttpResponse


# Schema View for Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Event Booking API",
        default_version='v1',
        description="""
# Event Booking System API Documentation

Welcome to the Event Booking System API! This comprehensive API provides event management, user authentication, RSVP handling, and external event integration capabilities.

## 🏗️ **System Architecture**

The API is organized into four main access levels, each providing different capabilities based on user roles:

### 🌐 **Public Endpoints (No Authentication Required)**
- **Event Discovery**: Browse events, categories, and tags
- **Basic Information**: Access public event details and listings
- **Search & Filter**: Find events by various criteria

### 🔐 **Authenticated User Endpoints (Login Required)**
- **Personal Management**: RSVP operations, profile management
- **Enhanced Data**: Access to personal event insights and statistics
- **User Interactions**: Reviews, ratings, and personal event history

### 🎯 **Organizer Endpoints (Organizer Role Required)**
- **Event Management**: Create, edit, and delete events
- **Analytics Dashboard**: Comprehensive event performance insights
- **Attendee Management**: Detailed attendee lists and management

### 👑 **Admin Endpoints (Staff/Superuser Required)**
- **System Administration**: User management and system analytics
- **Content Management**: Categories, tags, and platform content
- **Platform Analytics**: System-wide statistics and performance metrics

## 🔑 **Authentication**

This API uses JWT (JSON Web Token) authentication. Include your token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## 📚 **API Categories**

- **Accounts**: User authentication, registration, and profile management
- **Events**: Core event management with role-based access control
- **RSVP**: Attendance management and capacity control
- **External Events**: Integration with external event platforms

## 🚀 **Getting Started**

1. **Register**: Create an account at `/api/accounts/register/`
2. **Authenticate**: Login at `/api/accounts/login/` to get JWT tokens (access + refresh)
3. **Use JWT**: In Swagger, click "Authorize" and enter your JWT token (the "Bearer" prefix is added automatically)
4. **Refresh Token**: Use `/api/accounts/token/refresh/` when access token expires
5. **Explore**: Browse events at `/api/events/`
6. **Interact**: RSVP to events at `/api/rsvp/events/{id}/rsvp/`

## 📊 **Rate Limiting**

- **Anonymous Users**: 100 requests per hour
- **Authenticated Users**: 1000 requests per hour

## 🔒 **Security Features**

- JWT-based authentication with access and refresh tokens
- Role-based access control (RBAC)
- Rate limiting and throttling
- Input validation and sanitization
- CORS protection and security headers

For more detailed information, visit our [GitHub repository](https://github.com/yourusername/event-booking) or contact our support team.
        """,
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(
            name="Event Booking Support",
            email="support@eventbooking.com",
            url="https://github.com/yourusername/event-booking"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
        version="1.0.0",
        x_logo={
            "url": "https://via.placeholder.com/200x200/4F46E5/FFFFFF?text=EB",
            "backgroundColor": "#4F46E5"
        }
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('api/accounts/', include('accounts.urls')),
        path('api/events/', include('events.urls')),
        path('api/rsvp/', include('rsvp.urls')),
        path('api/external/', include('external_events.urls')),
    ]
)

urlpatterns = [
    # Home
    path('', lambda request: HttpResponse('''
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h1 style="color: #4F46E5;">🎉 Welcome to Event Booking API</h1>
            <p style="font-size: 18px; color: #6B7280;">
                A comprehensive event management platform with role-based access control
            </p>
            <div style="margin: 30px 0;">
                <a href="/api/docs/" style="background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 0 10px;">
                    📚 API Documentation
                </a>
                <a href="/api/redoc/" style="background: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 0 10px;">
                    📖 ReDoc
                </a>
            </div>
            <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
                <h3 style="color: #374151;">🚀 Quick Start</h3>
                <ul style="text-align: left; color: #6B7280;">
                    <li><strong>Public Access:</strong> Browse events without authentication</li>
                    <li><strong>User Registration:</strong> Create account for enhanced features</li>
                    <li><strong>Organizer Role:</strong> Manage and create events</li>
                    <li><strong>Admin Access:</strong> Full system administration</li>
                </ul>
            </div>
        </div>
    '''), name='home'),
    
    # Admin
    path('admin/', admin.site.urls),
    

    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/events/', include('events.urls')),
    path('api/rsvp/', include('rsvp.urls')),
    path('api/external/', include('external_events.urls')),
    
    # JSON Schema
    re_path(r'^api/schema(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
]   