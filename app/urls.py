from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Schema View for Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Event Booking API",
        default_version='v1',
        description="API documentation for Event Booking System with JWT authentication",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Home
    path('', lambda request: HttpResponse('<h1>Welcome to Event Booking API.</h1>'), name='home'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
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