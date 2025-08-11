from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as validate_email_format
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import User
from .serializers import UserSerializer
from .tasks import send_activation_email_async, send_password_reset_email_async

# Rate limit configurations
class AuthRateThrottle(AnonRateThrottle):
    rate = '5/hour'

class RegisterRateThrottle(AnonRateThrottle):
    rate = '3/hour'

# Helper functions
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Authentication Views
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
        
        activation_url = (
            f"{settings.FRONTEND_URL}/api/auth/verify-email/"
            f"?uid={uid}&token={token}&expires={expiration}"
        )
        
        send_activation_email_async.delay(user.email, activation_url)
        
        return Response(
            {'message': 'Registration successful. Please check your email to verify your account.'},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logout successful'})

# Email Verification Views
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    uid = request.query_params.get('uid')
    token = request.query_params.get('token')
    expires = request.query_params.get('expires')
    
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            if float(expires) < timezone.now().timestamp():
                return Response(
                    {'error': 'Token has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email_verified = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=['email_verified', 'email_verified_at'])
            return Response(
                {'message': 'Email verified successfully'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'error': 'Invalid or expired token'},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid user or token'},
            status=status.HTTP_400_BAD_REQUEST
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
        
        confirm_url = (
            f"{settings.FRONTEND_URL}/api/auth/verify-email/"
            f"?uid={uid}&token={token}&expires={expiration}"
        )
        
        send_activation_email.delay(user.email, confirm_url)
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
        
        reset_url = (
            f"{settings.FRONTEND_URL}/reset-password/"
            f"?uid={uid}&token={token}&expires={expiration}"
        )
        
        send_password_reset_email_async.delay(user.email, reset_url, user.first_name)
        return Response(
            {'message': 'Password reset email has been sent'},
            status=status.HTTP_200_OK
        )
        
    except User.DoesNotExist:
        # Don't reveal that the email doesn't exist
        return Response(
            {'message': 'If an account exists with this email, a password reset link has been sent'},
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def reset_password_confirm(request):
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not all([uidb64, token, new_password]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate password
        from django.contrib.auth.password_validation import validate_password
        validate_password(new_password)
        
        # Get user
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Check token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {'message': 'Password has been reset successfully'},
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