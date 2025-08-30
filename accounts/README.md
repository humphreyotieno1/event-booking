# Accounts App Documentation

## Overview

The Accounts app handles user authentication, registration, profile management, and role-based access control. It provides a secure foundation for the Event Booking system with JWT authentication, email verification, and user role management.

## 🏗️ **Architecture**

### **App Structure**
```
accounts/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py               # App configuration
├── models.py             # User model and related models
├── serializers.py        # DRF serializers for user operations
├── views.py              # Authentication and user management views
├── managers.py           # Custom user manager
├── signals.py            # Signal handlers for user operations
├── tasks.py              # Background tasks (email, notifications)
├── urls.py               # URL routing
├── tests.py              # Test suite
└── README.md             # This file
```

### **Dependencies**
- Django REST Framework
- Django REST Framework Simple JWT
- Django Extensions
- Pillow (for profile pictures)
- Celery (for background tasks)

## 👤 **User Model**

### **Custom User Model**
```python
class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.username
            
    def verify_email(self):
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['email_verified', 'email_verified_at'])
```

**Key Features**:
- **Role Management**: `is_organizer` flag for event creation privileges
- **Profile Enhancement**: Bio, phone number, and profile picture support
- **Email Verification**: Built-in email verification system
- **Extended Fields**: Additional user information beyond standard Django user

### **User Manager**
```python
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_organizer', True)
        return self.create_user(username, email, password, **extra_fields)
```

## 🔐 **Authentication System**

### **JWT Authentication**
```python
# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}
```

### **Authentication Endpoints**
- `POST /accounts/register/` - User registration
- `POST /accounts/login/` - User login (JWT token)
- `POST /accounts/logout/` - User logout
- `POST /accounts/refresh/` - Refresh JWT token
- `POST /accounts/verify-email/` - Email verification
- `POST /accounts/reset-password/` - Password reset request
- `POST /accounts/reset-password-confirm/` - Password reset confirmation

### **Security Features**
- **Password Validation**: Django's built-in password validation
- **Email Verification**: Required for full account access
- **JWT Blacklisting**: Secure token invalidation
- **Rate Limiting**: Protection against brute force attacks

## 🎯 **Views & Endpoints**

### **Authentication Views**

#### **User Registration**
```python
class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Send verification email
            send_verification_email.delay(user.id)
            return Response({
                'message': 'User registered successfully. Please check your email for verification.',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

#### **User Login**
```python
class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
```

### **Profile Management Views**

#### **User Profile**
```python
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

#### **Profile Picture Upload**
```python
class ProfilePictureView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if 'profile_picture' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        user.profile_picture = request.FILES['profile_picture']
        user.save()
        
        return Response({
            'message': 'Profile picture updated successfully',
            'profile_picture_url': user.profile_picture.url
        })
```

## 📧 **Email System**

### **Email Verification**
```python
@shared_task
def send_verification_email(user_id):
    user = User.objects.get(id=user_id)
    token = generate_verification_token(user)
    
    subject = 'Verify Your Email Address'
    message = f'''
    Hello {user.username},
    
    Please verify your email address by clicking the link below:
    {settings.FRONTEND_URL}/verify-email?token={token}
    
    If you didn't create this account, please ignore this email.
    '''
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
```

### **Password Reset**
```python
@shared_task
def send_password_reset_email(user_id):
    user = User.objects.get(id=user_id)
    token = generate_password_reset_token(user)
    
    subject = 'Reset Your Password'
    message = f'''
    Hello {user.username},
    
    You requested a password reset. Click the link below to reset your password:
    {settings.FRONTEND_URL}/reset-password?token={token}
    
    If you didn't request this, please ignore this email.
    '''
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
```

### **Email Templates**
- **Verification Email**: Account activation
- **Password Reset**: Secure password recovery
- **Welcome Email**: New user onboarding
- **Notification Emails**: System updates and alerts

## 🔑 **Role-Based Access Control**

### **User Roles**

#### **Regular Users**
- **Permissions**: Basic event browsing and RSVP
- **Access**: Personal profile and event interactions
- **Limitations**: Cannot create events

#### **Organizers**
- **Permissions**: Event creation and management
- **Access**: Enhanced event analytics and attendee management
- **Requirements**: Email verification required

#### **Administrators**
- **Permissions**: Full system access
- **Access**: User management and system analytics
- **Capabilities**: Role assignment and system configuration

### **Role Assignment**
```python
class RoleAssignmentView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        user_id = request.data.get('user_id')
        role = request.data.get('role')
        
        try:
            user = User.objects.get(id=user_id)
            if role == 'organizer':
                user.is_organizer = True
            elif role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            
            user.save()
            return Response({'message': f'Role {role} assigned successfully'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
```

## 📊 **User Analytics**

### **User Statistics**
```python
class UserAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        total_users = User.objects.count()
        organizers = User.objects.filter(is_organizer=True).count()
        verified_users = User.objects.filter(email_verified=True).count()
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return Response({
            'total_users': total_users,
            'organizers': organizers,
            'verified_users': verified_users,
            'active_users': active_users
        })
```

### **User Engagement Metrics**
- **Registration Trends**: New user signups over time
- **Verification Rates**: Email verification completion rates
- **Activity Patterns**: User login and engagement frequency
- **Role Distribution**: Organizer vs. regular user ratios

## 🚀 **Performance Optimizations**

### **Database Optimizations**
```python
# Optimized user queries
users = User.objects.select_related('profile').prefetch_related(
    'events', 'rsvps', 'reviews'
).filter(is_active=True)
```

### **Caching Strategy**
- **User Profiles**: Redis-cached user data
- **Authentication**: JWT token caching
- **Role Checks**: Permission caching for performance

### **Background Processing**
- **Email Sending**: Asynchronous email delivery via Celery
- **Image Processing**: Profile picture optimization
- **Data Aggregation**: User analytics computation

## 🧪 **Testing**

### **Test Structure**
```
tests/
├── test_models.py          # User model tests
├── test_views.py           # View and endpoint tests
├── test_serializers.py     # Serializer tests
├── test_authentication.py  # Authentication tests
├── test_permissions.py     # Permission tests
└── test_integration.py     # Integration tests
```

### **Running Tests**
```bash
# Test specific components
python manage.py test accounts.test_models
python manage.py test accounts.test_views
python manage.py test accounts.test_authentication

# Test entire app
python manage.py test accounts

# Test with coverage
coverage run --source='accounts' manage.py test accounts
coverage report
```

### **Test Examples**
```python
def test_user_registration(self):
    """Test user registration process."""
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'is_organizer': False
    }
    response = self.client.post('/accounts/register/', data)
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertTrue(User.objects.filter(username='testuser').exists())

def test_organizer_role_assignment(self):
    """Test organizer role assignment."""
    user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
    user.is_organizer = True
    user.save()
    self.assertTrue(user.is_organizer)
```

## 🔧 **Configuration**

### **Settings Integration**
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'accounts',
]

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### **URL Configuration**
```python
# Main app URLs
urlpatterns = [
    path('accounts/', include('accounts.urls')),
]
```

## 📚 **API Documentation**

### **Authentication Endpoints**

#### **User Registration**
```bash
POST /accounts/register/
Content-Type: application/json

{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword123",
    "is_organizer": false
}

# Response
{
    "message": "User registered successfully. Please check your email for verification.",
    "user_id": 123
}
```

#### **User Login**
```bash
POST /accounts/login/
Content-Type: application/json

{
    "username": "username",
    "password": "password"
}

# Response
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 123,
        "username": "username",
        "email": "user@example.com",
        "is_organizer": false
    }
}
```

#### **Profile Management**
```bash
GET /accounts/profile/
Authorization: Bearer <jwt_token>

# Response
{
    "id": 123,
    "username": "username",
    "email": "user@example.com",
    "bio": "Event enthusiast",
    "phone_number": "+1234567890",
    "profile_picture": "/media/profiles/user_pic.jpg",
    "is_organizer": false,
    "email_verified": true
}
```

## 🚨 **Error Handling**

### **Common Error Responses**
```python
# Validation Error
{
    "error": "Invalid registration data",
    "details": {
        "username": ["This username is already taken"],
        "email": ["Enter a valid email address"]
    }
}

# Authentication Error
{
    "error": "Invalid credentials",
    "status_code": 401
}

# Permission Error
{
    "error": "Access denied. Admin privileges required.",
    "status_code": 403
}
```

### **Custom Exception Handling**
- **Validation Errors**: Field-level error messages
- **Authentication Errors**: Clear login/registration feedback
- **Permission Errors**: Role-based access messages
- **Business Logic Errors**: Contextual error information

## 🔮 **Future Enhancements**

### **Planned Features**
- **Social Authentication**: OAuth2 integration (Google, Facebook, GitHub)
- **Two-Factor Authentication**: Enhanced security with 2FA
- **Advanced Profiles**: Extended user information and preferences
- **User Groups**: Organization and team management

### **Security Improvements**
- **Password Policies**: Configurable password requirements
- **Account Lockout**: Brute force protection
- **Session Management**: Advanced session controls
- **Audit Logging**: User action tracking

### **Performance Enhancements**
- **User Caching**: Redis-based user data caching
- **Background Processing**: Asynchronous user operations
- **Database Optimization**: Advanced query optimization
- **CDN Integration**: Profile picture delivery optimization

## 📞 **Support & Contributing**

### **Getting Help**
- **Documentation**: Check this README and main project README
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join GitHub Discussions for questions

### **Contributing**
- **Code Style**: Follow PEP 8 and Django conventions
- **Testing**: Maintain >90% test coverage
- **Documentation**: Update docs for all new features
- **Security**: Follow security best practices

---

**Accounts App** - The foundation of the Event Booking system, providing secure user authentication, role management, and profile capabilities.
