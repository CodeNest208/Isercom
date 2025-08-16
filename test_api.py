#!/usr/bin/env python3
"""
Test script to validate API endpoints
"""
import requests
import json
from requests.sessions import Session

def test_api_endpoints():
    base_url = 'http://127.0.0.1:8000'
    session = Session()
    
    print("=== API Implementation Testing ===\n")
    
    # Test 1: Home API
    print("1. Testing Home API...")
    try:
        response = session.get(f'{base_url}/api/home/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   Message: {data.get('data', {}).get('message', 'No message')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Auth Check API (unauthenticated)
    print("\n2. Testing Auth Check API (unauthenticated)...")
    try:
        response = session.get(f'{base_url}/api/auth/check/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Authenticated: {data.get('is_authenticated', False)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get CSRF Token from main page
    print("\n3. Getting CSRF Token...")
    try:
        response = session.get(f'{base_url}/')
        csrf_token = None
        for cookie in session.cookies:
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value
                break
        print(f"   CSRF Token: {'Found' if csrf_token else 'Not found'}")
    except Exception as e:
        print(f"   Error: {e}")
        csrf_token = None
    
    # Test 4: Login API with existing user
    print("\n4. Testing Login API...")
    try:
        login_data = {
            'email': 'odimer@gmail.com',  # Known user from database
            'password': 'test123'  # Test password
        }
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        } if csrf_token else {'Content-Type': 'application/json'}
        
        response = session.post(f'{base_url}/api/auth/login/', 
                               data=json.dumps(login_data),
                               headers=headers)
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        print(f"   Message: {data.get('message', 'No message')}")
        if data.get('errors'):
            print(f"   Errors: {data['errors']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Register API structure
    print("\n5. Testing Register API structure...")
    try:
        register_data = {
            'username': 'testuser123',
            'email': 'testuser123@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '1234567890',
            'date_of_birth': '1990-01-01',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'terms_agreement': True
        }
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        } if csrf_token else {'Content-Type': 'application/json'}
        
        response = session.post(f'{base_url}/api/auth/register/', 
                               data=json.dumps(register_data),
                               headers=headers)
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Success: {data.get('success', False)}")
        print(f"   Message: {data.get('message', 'No message')}")
        if data.get('errors'):
            print(f"   Errors: {list(data['errors'].keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== Testing Complete ===")

if __name__ == "__main__":
    test_api_endpoints()
