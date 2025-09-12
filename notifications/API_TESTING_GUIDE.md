# Notifications API Testing Guide

## API Endpoints Overview

### Admin Endpoints (Requires admin authentication)
- `GET /api/notifications/admin/` - List all notifications
- `POST /api/notifications/admin/` - Create new notification
- `GET /api/notifications/admin/{id}/` - Get specific notification
- `PUT /api/notifications/admin/{id}/` - Update notification
- `DELETE /api/notifications/admin/{id}/` - Delete notification
- `GET /api/notifications/admin/stats/` - Get notification statistics
- `GET /api/notifications/admin/{id}/readers/` - Get users who read notification
- `POST /api/notifications/admin/{id}/duplicate/` - Duplicate notification

### User Endpoints (Requires user authentication)
- `GET /api/notifications/user/` - List user's notifications
- `GET /api/notifications/user/{id}/` - Get specific notification
- `POST /api/notifications/user/mark_as_read/` - Mark notifications as read
- `GET /api/notifications/user/unread_count/` - Get unread count
- `GET /api/notifications/user/unread/` - Get only unread notifications

## Sample Data Structures

### Creating a Notification (Admin)
```json
{
    "title": "Welcome to BuildMart!",
    "notification_type": "announcement",
    "priority": "medium",
    "target_audience": "all_users",
    "message": "Welcome to our platform. Start exploring amazing building materials!",
    "action_buttons": [
        {
            "text": "Browse Products",
            "url": "/products"
        },
        {
            "text": "Learn More",
            "url": "/about"
        }
    ],
    "created_by": "admin",
    "is_active": true
}
```

### Creating a Notification for Specific Users
```json
{
    "title": "Seller Verification Required",
    "notification_type": "alert",
    "priority": "high",
    "target_audience": "specific_users",
    "specific_user_ids": ["user-uuid-1", "user-uuid-2"],
    "message": "Please complete your seller verification to start selling products.",
    "action_buttons": [
        {
            "text": "Complete Verification",
            "url": "/seller/verify"
        }
    ],
    "created_by": "admin"
}
```

### Marking Notifications as Read
```json
{
    "notification_ids": ["notification-uuid-1", "notification-uuid-2"],
    "clicked": false
}
```

### Marking with Click Tracking
```json
{
    "notification_ids": ["notification-uuid-1"],
    "clicked": true
}
```

## Testing Steps

1. **Start Django Server**
   ```bash
   cd backend
   .\venv\Scripts\activate
   python manage.py runserver
   ```

2. **Create Test Users**
   ```bash
   python manage.py createsuperuser --email admin@buildmart.com --username admin
   ```

3. **Access Django Admin**
   - Go to http://127.0.0.1:8000/admin/
   - Login with superuser credentials
   - Navigate to Notifications section

4. **Test API Endpoints**
   - Use tools like Postman, curl, or Django's browsable API
   - Base URL: http://127.0.0.1:8000/api/notifications/

## Expected Behavior

### For Admins:
- Can create, read, update, delete all notifications
- Can view detailed statistics
- Can see who has read each notification
- Can duplicate existing notifications

### For Users:
- Can only see notifications targeted to them based on:
  - target_audience = "all_users"
  - target_audience = "sellers" (if user.role = "seller")
  - target_audience = "buyers" (if user.role = "user")
  - target_audience = "specific_users" (if user is in specific_users list)
- Can mark notifications as read
- Can track click events on action buttons
- Can get unread count and filter by unread status

### Statistics Include:
- Total notifications sent
- Read rate percentage
- Click rate percentage  
- Pending notifications count
- Breakdown by type, priority, and target audience

## Frontend Integration Notes

The backend is now ready for frontend integration. Next steps:
1. Create notification components for buyer/seller dashboards
2. Implement notification badge with unread count
3. Add mark-as-read functionality
4. Handle action button clicks with tracking
5. Admin dashboard for notification management
