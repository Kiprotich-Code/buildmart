#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buildmart.settings')
try:
    django.setup()
    
    from notifications.models import Notification
    from accounts.models import CustomUser
    
    print(f"Total notifications: {Notification.objects.count()}")
    print(f"Total users: {CustomUser.objects.count()}")
    
    # Check notifications by target audience
    all_notifications = Notification.objects.all()
    for notif in all_notifications:
        print(f"Notification: {notif.title}, Target: {notif.target_audience}")
        if notif.target_audience == 'specific_users':
            print(f"  - Specific users count: {notif.specific_users.count()}")
    
    seller_notifications = Notification.objects.filter(target_audience="sellers")
    print(f"Notifications for sellers: {seller_notifications.count()}")
    
    all_user_notifications = Notification.objects.filter(target_audience="all_users")
    print(f"Notifications for all users: {all_user_notifications.count()}")
    
    # Check seller users
    sellers = CustomUser.objects.filter(role='seller')
    print(f"Total sellers: {sellers.count()}")
    buyers = CustomUser.objects.filter(role='user') 
    print(f"Total buyers: {buyers.count()}")
    admins = CustomUser.objects.filter(role='admin')
    print(f"Total admins: {admins.count()}")
    
    # Show some user details
    print("\nUser roles breakdown:")
    for user in CustomUser.objects.all()[:10]:
        print(f"  {user.email}: {user.role}")
    
    # Check what specific users are targeted
    specific_notifications = Notification.objects.filter(target_audience='specific_users')
    for notif in specific_notifications:
        print(f"\nSpecific notification '{notif.title}' targets:")
        for user in notif.specific_users.all():
            print(f"  - {user.email} ({user.role})")
    
except Exception as e:
    print(f"Error: {e}")
