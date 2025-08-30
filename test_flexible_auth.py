#!/usr/bin/env python3
"""
Test script to verify that the flexible JWT authentication is working.
This tests whether the Bearer prefix is automatically added when missing.
"""

import os
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from app.authentication import FlexibleJWTAuthentication
from rest_framework.test import APIRequestFactory

User = get_user_model()

def test_flexible_jwt_authentication():
    """Test that the flexible JWT authentication automatically adds Bearer prefix"""
    print("🔐 Testing Flexible JWT Authentication...")
    
    try:
        # Create or get a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'testuser@example.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Generate JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        print(f"✅ Generated JWT token: {access_token[:50]}...")
        
        # Test 1: Token without Bearer prefix
        print("\n🧪 Test 1: Token without Bearer prefix")
        factory = APIRequestFactory()
        request = factory.get('/test/', HTTP_AUTHORIZATION=access_token)
        
        # Test the flexible authentication
        auth = FlexibleJWTAuthentication()
        user_auth_tuple = auth.authenticate(request)
        
        if user_auth_tuple:
            user, auth = user_auth_tuple
            print(f"✅ Authentication successful with token without Bearer prefix!")
            print(f"   User: {user.username}")
            print(f"   Updated header: {request.META.get('HTTP_AUTHORIZATION', 'Not found')}")
        else:
            print("❌ Authentication failed with token without Bearer prefix")
        
        # Test 2: Token with Bearer prefix
        print("\n🧪 Test 2: Token with Bearer prefix")
        request2 = factory.get('/test/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
        user_auth_tuple2 = auth.authenticate(request2)
        
        if user_auth_tuple2:
            user2, auth2 = user_auth_tuple2
            print(f"✅ Authentication successful with token with Bearer prefix!")
            print(f"   User: {user2.username}")
        else:
            print("❌ Authentication failed with token with Bearer prefix")
        
        # Test 3: API endpoint with token without Bearer prefix
        print("\n🧪 Test 3: API endpoint with token without Bearer prefix")
        url = "http://localhost:8000/api/events/admin/categories/"
        headers = {
            'Authorization': access_token,  # No Bearer prefix
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        print(f"✅ API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API call successful with token without Bearer prefix!")
            print("   The flexible authentication is working correctly!")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing flexible authentication: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🚀 Starting Flexible JWT Authentication Tests...\n")
    
    test_flexible_jwt_authentication()
    
    print("\n🎯 Flexible authentication tests completed!")

if __name__ == "__main__":
    main()
