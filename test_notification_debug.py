#!/usr/bin/env python3
"""
Test script for notification creation to debug the specific users issue
"""
import requests
import json

# Test data
test_data = {
    "title": "Test Notification",
    "notification_type": "announcement",
    "priority": "medium",
    "target_audience": "specific_users",
    "specific_user_ids": [1, 2, 3],  # Use integers instead of strings
    "message": "This is a test notification for specific users",
    "action_buttons": [],
    "created_by": "admin",
    "is_active": True
}

def test_notification_creation():
    url = "http://127.0.0.1:8000/api/notifications/admin/"
    
    print("Testing notification creation...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("Validation Error:")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print("Response text:", response.text)
        else:
            print("Response:", response.json())
            
    except Exception as e:
        print(f"Error: {e}")

def test_with_valid_user_ids():
    # First, let's get some actual user IDs from the API
    url = "http://127.0.0.1:8000/api/accounts/admin/users/"
    
    print("\nFetching actual user IDs...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users")
            
            if users:
                # Use first few user IDs as integers
                user_ids = [int(user['id']) for user in users[:3]]
                print(f"Using user IDs: {user_ids}")
                
                # Test with actual user IDs
                test_data_with_real_ids = test_data.copy()
                test_data_with_real_ids['specific_user_ids'] = user_ids
                
                print("\nTesting with real user IDs...")
                notif_response = requests.post("http://127.0.0.1:8000/api/notifications/admin/", 
                                             json=test_data_with_real_ids)
                print(f"Status Code: {notif_response.status_code}")
                
                if notif_response.status_code == 400:
                    print("Validation Error:")
                    try:
                        error_data = notif_response.json()
                        print(json.dumps(error_data, indent=2))
                    except:
                        print("Response text:", notif_response.text)
                else:
                    print("Success! Response:", notif_response.json())
            else:
                print("No users found")
        else:
            print(f"Failed to fetch users: {response.status_code}")
    except Exception as e:
        print(f"Error fetching users: {e}")

if __name__ == "__main__":
    test_notification_creation()
    test_with_valid_user_ids()
