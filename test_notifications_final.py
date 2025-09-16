#!/usr/bin/env python3
"""
Test script to verify notification creation for specific users
"""
import requests
import json

def test_specific_users_notification():
    """Test creating a notification for specific users"""
    url = "http://127.0.0.1:8000/api/notifications/admin/"
    
    # Test data for specific users
    test_data = {
        "title": "Test - Specific Users Notification",
        "notification_type": "announcement",
        "priority": "high",
        "target_audience": "specific_users",
        "specific_user_ids": [1, 2, 3, 4, 5],  # Using integer IDs as fixed
        "message": "This is a test notification sent to specific users after applying all fixes",
        "action_buttons": [
            {
                "text": "View Dashboard",
                "url": "/dashboard"
            },
            {
                "text": "Contact Support",
                "url": "/support"
            }
        ],
        "created_by": "admin",
        "is_active": True
    }
    
    print("🧪 Testing Notification Creation for Specific Users")
    print("=" * 60)
    print(f"📡 API Endpoint: {url}")
    print(f"📊 Test Data:")
    print(json.dumps(test_data, indent=2))
    print("\n" + "=" * 60)
    
    try:
        print("⏳ Sending request...")
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 201:
            # Success!
            result = response.json()
            print("🎉 SUCCESS! Notification created successfully!")
            print("\n📋 Response Details:")
            print(f"   🆔 ID: {result.get('id', 'N/A')}")
            print(f"   📝 Title: {result.get('title', 'N/A')}")
            print(f"   🎯 Target: {result.get('target_audience', 'N/A')}")
            print(f"   👥 Recipients: {result.get('total_recipients', 'N/A')}")
            print(f"   📧 Specific Users: {len(result.get('specific_users', []))}")
            
            if result.get('specific_users'):
                print("\n👤 Targeted Users:")
                for i, user in enumerate(result.get('specific_users', [])[:3]):
                    print(f"   {i+1}. {user.get('email', 'N/A')} ({user.get('role', 'N/A')})")
                if len(result.get('specific_users', [])) > 3:
                    print(f"   ... and {len(result.get('specific_users', [])) - 3} more")
            
            print("\n✨ All fixes are working correctly!")
            
        elif response.status_code == 400:
            # Validation error
            try:
                error_data = response.json()
                print("❌ VALIDATION ERROR:")
                print(json.dumps(error_data, indent=2))
            except:
                print("❌ Validation error (couldn't parse JSON)")
                print(f"Response text: {response.text}")
                
        elif response.status_code == 500:
            print("💥 SERVER ERROR:")
            print(f"Response text: {response.text}")
            
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR: Could not connect to Django server")
        print("Make sure the server is running on http://127.0.0.1:8000/")
        
    except Exception as e:
        print(f"💀 UNEXPECTED ERROR: {e}")

def test_all_users_notification():
    """Test creating a notification for all users (should work)"""
    url = "http://127.0.0.1:8000/api/notifications/admin/"
    
    test_data = {
        "title": "Test - All Users Notification",
        "notification_type": "system",
        "priority": "medium",
        "target_audience": "all_users",
        "message": "This is a test notification for all users",
        "created_by": "admin",
        "is_active": True
    }
    
    print("\n\n🌐 Testing Notification Creation for All Users (Control Test)")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("🎉 SUCCESS! All users notification created!")
            print(f"   👥 Recipients: {result.get('total_recipients', 'N/A')}")
        else:
            print("❌ Failed to create all users notification")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"💀 Error: {e}")

if __name__ == "__main__":
    test_specific_users_notification()
    test_all_users_notification()
    
    print("\n" + "=" * 60)
    print("🏁 Test Complete!")
    print("=" * 60)