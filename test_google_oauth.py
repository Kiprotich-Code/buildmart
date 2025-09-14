#!/usr/bin/env python3
"""
Test script for Google OAuth endpoint
"""
import requests
import json

# Test the Google OAuth endpoint
def test_google_oauth():
    url = "http://127.0.0.1:8000/api/accounts/auth/google/"
    
    # Test with invalid token
    test_data = {
        "access_token": "invalid_token_for_testing"
    }
    
    print("Testing Google OAuth endpoint...")
    print(f"URL: {url}")
    print(f"Data: {test_data}")
    
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Django server. Make sure it's running on http://127.0.0.1:8000/")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_google_oauth()
