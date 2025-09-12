#!/usr/bin/env python3
"""
Test script for Recent Activities API endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_admin_activities():
    """Test admin activities endpoint"""
    print("=" * 50)
    print("Testing Admin Activities Endpoint")
    print("=" * 50)
    

    url = f"{BASE_URL}/api/activities/admin/activities/"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Number of activities: {len(data)}")
            for activity in data[:3]:  # Show first 3
                print(f"- {activity.get('action_type')}: {activity.get('message')[:50]}...")
        elif response.status_code == 403:
            print("Access denied - authentication required")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_buyer_activities():
    """Test buyer activities endpoint"""
    print("\n" + "=" * 50)
    print("Testing Buyer Activities Endpoint")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/activities/buyer/activities/"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Number of buyer activities: {len(data)}")
            for activity in data:
                print(f"- {activity.get('action_type')}: {activity.get('message')[:50]}...")
        elif response.status_code == 403:
            print("Access denied - authentication required")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_activity_stats():
    """Test activity stats endpoint"""
    print("\n" + "=" * 50)
    print("Testing Activity Stats Endpoint")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/activities/admin/stats/"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Today's total activities: {data.get('today_total')}")
            print("Activity stats:")
            for key, value in data.get('stats', {}).items():
                print(f"- {value.get('display_name')}: {value.get('count')}")
        elif response.status_code == 403:
            print("Access denied - authentication required")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_endpoint_access():
    """Test basic endpoint access"""
    print("\n" + "=" * 50)
    print("Testing Basic Endpoint Access")
    print("=" * 50)
    
    endpoints = [
        "/api/activities/admin/activities/",
        "/api/activities/buyer/activities/",
        "/api/activities/admin/stats/",
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url)
            print(f"{endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

if __name__ == "__main__":
    print("Testing Recent Activities API")
    test_endpoint_access()
    test_admin_activities()
    test_buyer_activities()
    test_activity_stats()
