from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Admin site customization
admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Event Booking Admin')
admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Event Booking Admin Portal')
admin.site.index_title = getattr(settings, 'ADMIN_SITE_INDEX_TITLE', 'Welcome to Event Booking Administration')

# Schema View for Swagger/OpenAPI - Best Practices
schema_view = get_schema_view(
    openapi.Info(
        title="🎉 Event Booking API",
        default_version='v1.0',
        description="""
# 🚀 **Event Booking API v1.0**

A modern, scalable event management platform built with Django REST Framework and comprehensive role-based access control.

## 🏗️ **Architecture Overview**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Django 5.2 + DRF | RESTful API with advanced features |
| **Database** | PostgreSQL | Robust data storage with advanced querying |
| **Authentication** | JWT (SimpleJWT) | Secure token-based authentication |
| **Background Tasks** | Celery + Redis | Asynchronous processing |
| **Caching** | Redis | Performance optimization |
| **Documentation** | OpenAPI 3.0 | Interactive API documentation |

## 🔐 **Access Control Matrix**

| Endpoint Type | Authentication | User Role | Description |
|---------------|----------------|-----------|-------------|
| **Public** | ❌ None | 👥 Everyone | Event discovery, categories, tags |
| **Authenticated** | ✅ JWT Token | 👤 Registered Users | RSVP, reviews, enhanced data |
| **Organizer** | ✅ JWT Token | 🎯 Event Organizers | Event management, analytics |
| **Admin** | ✅ JWT Token | 👑 Administrators | System management, full access |

## 🚀 **Quick Start Guide**

### 1. **Authentication Flow**
```bash
# Register new account
POST /api/accounts/register/
{
  "username": "your_username",
  "email": "your_email@example.com",
  "password": "your_password"
}

# Login to get JWT tokens
POST /api/accounts/login/
{
  "username": "your_username",
  "password": "your_password"
}

# Response includes access and refresh tokens
{
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### 2. **Using JWT in Swagger**
1. Click the **🔒 Authorize** button at the top
2. Enter your JWT token (without "Bearer" prefix)
3. Click **Authorize**
4. The system automatically adds the "Bearer " prefix

### 3. **Token Refresh**
```bash
POST /api/accounts/token/refresh/
{
  "refresh": "your_refresh_token"
}
```

## 📊 **API Categories**

- **🔓 Public**: Event discovery, categories, tags
- **🔐 Authentication**: Registration, login, password management
- **👤 User Management**: Profile management, account settings
- **🎉 Events**: Core event CRUD operations
- **🎯 Organizer**: Event management and analytics
- **👑 Admin**: System administration and analytics
- **✅ RSVP**: Attendance management and tracking
- **🌐 External Events**: Third-party platform integration

## 🔒 **Security Features**

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Granular permission system
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive data sanitization
- **CORS Protection**: Cross-origin request security
- **HTTPS Ready**: Production security compliance

## 📈 **Performance Features**

- **Database Optimization**: Advanced querying with Django ORM
- **Caching Layer**: Redis-based performance enhancement
- **Asynchronous Processing**: Celery background tasks
- **Pagination**: Efficient data retrieval
- **Filtering & Search**: Advanced data querying

## 🛠️ **Development & Testing**

- **Unit Tests**: Comprehensive test coverage
- **Integration Tests**: API endpoint testing
- **Performance Testing**: Load and stress testing
- **Documentation**: Auto-generated OpenAPI specs

## 📚 **Additional Resources**

- **GitHub Repository**: [Event Booking Platform](https://github.com/yourusername/event-booking)
- **API Status**: [Health Check Endpoint](/api/health/)
- **Support**: support@eventbooking.com
- **Documentation**: [Full API Reference](https://docs.eventbooking.com)

---

*Built with ❤️ using Django REST Framework and modern web technologies*
        """,
        terms_of_service="https://eventbooking.com/terms/",
        contact=openapi.Contact(
            name="Event Booking Support Team",
            email="support@eventbooking.com",
            url="https://eventbooking.com/support"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
        version="1.0.0",
        x_logo={
            "url": "https://via.placeholder.com/200x200/4F46E5/FFFFFF?text=🎉",
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

# Health check view
@csrf_exempt
def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': '2025-01-27T12:00:00Z',
        'service': 'Event Booking API',
        'version': '1.0.0'
    })

urlpatterns = [
    # Health check
    path('health/', health_check, name='health_check'),
    
    # Home
    path('', lambda request: HttpResponse('''
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h1 style="color: #4F46E5;">🎉 Event Booking API v1.0</h1>
            <p style="font-size: 18px; color: #6B7280;">
                A modern, scalable event management platform with comprehensive role-based access control
            </p>
            <div style="margin: 30px 0;">
                <a href="/api/docs/" style="background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 0 10px;">
                    📚 Swagger UI
                </a>
                <a href="/api/redoc/" style="background: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 0 10px;">
                    📖 ReDoc
                </a>
            </div>
            <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; max-width: 700px; margin: 0 auto;">
                <h3 style="color: #374151;">🚀 Quick Start Guide</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: left; color: #6B7280;">
                    <div>
                        <h4 style="color: #4F46E5;">🔐 Authentication</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Register at <code>/api/accounts/register/</code></li>
                            <li>Login at <code>/api/accounts/login/</code></li>
                            <li>Use JWT tokens for protected endpoints</li>
                        </ul>
                    </div>
                    <div>
                        <h4 style="color: #10B981;">🎯 Access Levels</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Public:</strong> Browse events & categories</li>
                            <li><strong>Authenticated:</strong> RSVP & reviews</li>
                            <li><strong>Organizer:</strong> Event management</li>
                            <li><strong>Admin:</strong> System administration</li>
                        </ul>
                    </div>
                </div>
            </div>
            <div style="margin-top: 30px; padding: 20px; background: #EFF6FF; border-radius: 8px; max-width: 700px; margin-left: auto; margin-right: auto;">
                <h3 style="color: #1E40AF;">💡 Pro Tips</h3>
                <p style="color: #374151; margin: 0;">
                    <strong>JWT Authentication:</strong> In Swagger, click "Authorize" and enter your token without the "Bearer" prefix - it's added automatically! 🎯
                </p>
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