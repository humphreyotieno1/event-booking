from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from . import views

# Schema View for Account-specific API docs
account_schema_view = get_schema_view(
    openapi.Info(
        title="Account Management API",
        default_version='v1',
        description="Account management endpoints for Event Booking System",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[path('api/accounts/', include('accounts.urls'))],
)

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    
    # Email Verification
    path('verify-email/', views.verify_email, name='verify-email'),
    path('resend-verification/', views.resend_verification_email, name='resend-verification'),
    
    # Password Reset
    path('reset-password/', views.reset_password_request, name='reset-password-request'),
    path('reset-password/confirm/', views.reset_password_confirm, name='reset-password-confirm'),
    path('reset-password/verify/', views.reset_password_verify, name='reset_password_verify'),  # NEW - for GET requests
    
    # User Profile
    path('profile/', views.user_profile, name='user-profile'),
    
    # Validation
    path('validate-email/', views.validate_email_view, name='validate-email'),
    
    # API Documentation
    path('docs/', account_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', account_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]