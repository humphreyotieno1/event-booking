from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as validate_email_format
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User
from .serializers import UserSerializer
from .tasks import send_activation_email_async, send_password_reset_email_async

# Rate limit configurations
class AuthRateThrottle(AnonRateThrottle):
    rate = '5/hour'

class RegisterRateThrottle(AnonRateThrottle):
    rate = '5/hour'

# Helper functions
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Authentication Views
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password', format='password'),
        },
    ),
    responses={
        200: openapi.Response(description='Login successful'),
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Both username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=username, password=password)
    
    if user is None:
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Account is not active. Please verify your email.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    login(request, user)
    tokens = get_tokens_for_user(user)
    return Response({
        'message': 'Login successful',
        'tokens': tokens,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_organizer': user.is_organizer
        }
    })

@swagger_auto_schema(
    method='post',
    request_body=UserSerializer,
    responses={
        201: openapi.Response(description='Registration successful'),
        400: 'Bad Request',
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register_view(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate activation link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        expiration = (timezone.now() + timedelta(hours=24)).timestamp()
        
        activation_url = f"{settings.FRONTEND_URL}/api/accounts/verify-email/?" + \
                       f"uid={uid}&token={token}&expires={expiration}"
        
        send_activation_email_async.delay(user.email, activation_url)
        
        return Response(
            {'message': 'Registration successful. Please check your email to verify your account.'},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Email Verification Views
@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('uid', openapi.IN_QUERY, description='User ID', type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('token', openapi.IN_QUERY, description='Verification token', type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('expires', openapi.IN_QUERY, description='Expiration timestamp', type=openapi.TYPE_STRING, required=True),
    ],
    responses={
        200: openapi.Response(description='Email verified successfully'),
        400: 'Bad Request',
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    uid = request.query_params.get('uid')
    token = request.query_params.get('token')
    expires = request.query_params.get('expires')
    
    if not all([uid, token, expires]):
        return Response(
            {'error': 'Missing required parameters (uid, token, or expires)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check expiration first
        try:
            expiration_time = float(expires)
            if expiration_time < timezone.now().timestamp():
                return Response(
                    {'error': 'Verification link has expired. Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid expiration time in verification link.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decode and get user
        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid verification link. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired verification link. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If we get here, all checks passed - verify the email
        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.is_active = True  # Activate the user account
        user.save(update_fields=['email_verified', 'email_verified_at', 'is_active'])
        
        return Response(
            {'message': 'Email verified successfully. Your account is now active.'},
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': 'An error occurred while processing your request. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address', format='email'),
        },
    ),
    responses={
        200: openapi.Response(description='Verification email has been resent'),
        400: 'Bad Request',
        404: 'Not Found',
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def resend_verification_email(request):
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        if user.email_verified:
            return Response(
                {'message': 'Email is already verified'},
                status=status.HTTP_200_OK
            )
        
        # Generate new verification token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        expiration = (timezone.now() + timedelta(hours=24)).timestamp()
        
        confirm_url = f"{settings.FRONTEND_URL}/api/accounts/verify-email/?" + \
                    f"uid={uid}&token={token}&expires={expiration}"
        
        send_activation_email_async.delay(user.email, confirm_url)
        return Response(
            {'message': 'Verification email has been resent'},
            status=status.HTTP_200_OK
        )
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User with this email does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )

# Password Reset Views
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address', format='email'),
        },
    ),
    responses={
        200: openapi.Response(description='Password reset email has been sent'),
        400: 'Bad Request',
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def reset_password_request(request):
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        expiration = (timezone.now() + timedelta(hours=1)).timestamp()
        
        # URL for the verification endpoint (GET request)
        reset_url = f"{settings.FRONTEND_URL}/api/accounts/reset-password/verify/?" + \
                  f"uid={uid}&token={token}&expires={expiration}"
        
        send_password_reset_email_async.delay(user.email, reset_url, user.first_name or '')
        
    except User.DoesNotExist:
        pass  # Don't reveal that the email doesn't exist
    
    # Always return success message for security
    return Response(
        {'message': 'If an account exists with this email, a password reset link has been sent'},
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('uid', openapi.IN_QUERY, description='User ID', type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('token', openapi.IN_QUERY, description='Password reset token', type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('expires', openapi.IN_QUERY, description='Expiration timestamp', type=openapi.TYPE_STRING, required=True),
    ],
    responses={
        200: openapi.Response(
            description='Token is valid, ready for password reset',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'uid': openapi.Schema(type=openapi.TYPE_STRING),
                    'token': openapi.Schema(type=openapi.TYPE_STRING),
                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                    'username': openapi.Schema(type=openapi.TYPE_STRING),
                    'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Bad Request - Invalid or expired token',
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def reset_password_verify(request):
    """Verify the password reset token from email link"""
    uid = request.query_params.get('uid')
    token = request.query_params.get('token')
    expires = request.query_params.get('expires')
    
    if not all([uid, token, expires]):
        return Response(
            {'error': 'Missing required parameters (uid, token, or expires)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check expiration first
        try:
            expiration_time = float(expires)
            if expiration_time < timezone.now().timestamp():
                return Response(
                    {'error': 'Password reset link has expired. Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid expiration time in reset link.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Decode and get user
        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired reset link. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Token is valid - return user info for form
        return Response(
            {
                'message': 'Token is valid. You can now reset your password.',
                'uid': uid,
                'token': token,
                'email': user.email,
                'username': user.username,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', '')
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        return Response(
            {'error': 'An error occurred while processing your request. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['uid', 'token', 'new_password'],
        properties={
            'uid': openapi.Schema(type=openapi.TYPE_STRING, description='User ID'),
            'token': openapi.Schema(type=openapi.TYPE_STRING, description='Password reset token'),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='New password', format='password'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='Confirm new password', format='password'),
        },
    ),
    responses={
        200: openapi.Response(description='Password has been reset successfully'),
        400: 'Bad Request',
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def reset_password_confirm(request):
    """Confirm the password reset with new password"""
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not all([uidb64, token, new_password]):
        return Response(
            {'error': 'Missing required fields: uid, token, and new_password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check password confirmation if provided
    if confirm_password and new_password != confirm_password:
        return Response(
            {'error': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate password strength
        from django.contrib.auth.password_validation import validate_password
        validate_password(new_password)
        
        # Get user
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Check token (this validates the token is still valid)
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {'message': 'Password has been reset successfully. You can now login with your new password.'},
            status=status.HTTP_200_OK
        )
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid user or token'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except ValidationError as e:
        return Response(
            {'error': e.messages},
            status=status.HTTP_400_BAD_REQUEST
        )

# User Management Views
@swagger_auto_schema(
    method='get',
    responses={
        200: UserSerializer,
        401: 'Unauthorized',
    },
    security=[{"Bearer": []}]
)
@swagger_auto_schema(
    method='put',
    request_body=UserSerializer,
    responses={
        200: UserSerializer,
        400: 'Bad Request',
        401: 'Unauthorized',
    },
    security=[{"Bearer": []}]
)
@swagger_auto_schema(
    method='delete',
    responses={
        204: 'No Content',
        401: 'Unauthorized',
    },
    security=[{"Bearer": []}]
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
        
    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Email Validation
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address to validate', format='email'),
        },
    ),
    responses={
        200: openapi.Response(
            description='Validation result',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Bad Request',
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def validate_email_view(request):
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        validate_email_format(email)
        if User.objects.filter(email=email).exists():
            return Response(
                {'available': False, 'message': 'Email is already in use'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'available': True, 'message': 'Email is available'},
            status=status.HTTP_200_OK
        )
    except ValidationError:
        return Response(
            {'available': False, 'message': 'Invalid email format'},
            status=status.HTTP_400_BAD_REQUEST
        )