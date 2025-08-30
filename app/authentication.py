from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.translation import gettext_lazy as _


class FlexibleJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that automatically adds 'Bearer ' prefix if missing.
    This makes Swagger UI easier to use by allowing users to enter just the token.
    """
    
    def get_header(self, request):
        """
        Get the authorization header from the request.
        Automatically add 'Bearer ' prefix if it's missing.
        """
        header = super().get_header(request)
        
        if header:
            # Convert to string if it's bytes
            if isinstance(header, bytes):
                header = header.decode('utf-8')
            
            if not header.startswith('Bearer '):
                # If the header doesn't start with 'Bearer ', add it
                header = f'Bearer {header}'
                # Update the request header for future use
                request.META['HTTP_AUTHORIZATION'] = header
            
        return header
    
    def authenticate(self, request):
        """
        Authenticate the request using JWT token.
        """
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError) as e:
            # Log the error for debugging
            print(f"JWT Authentication Error: {e}")
            return None
