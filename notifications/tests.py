from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Notification, NotificationRead

User = get_user_model()


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='user'
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='adminuser',
            password='adminpass123',
            role='admin'
        )
        
    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            title='Test Notification',
            notification_type='announcement',
            priority='medium',
            target_audience='all_users',
            message='This is a test notification',
            created_by='admin',
            created_by_user=self.admin_user
        )
        
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.notification_type, 'announcement')
        self.assertEqual(str(notification), 'Test Notification (announcement)')
        
    def test_notification_read_tracking(self):
        """Test notification read tracking"""
        notification = Notification.objects.create(
            title='Test Notification',
            notification_type='alert',
            priority='high',
            target_audience='all_users',
            message='This is a test notification',
            created_by='admin',
            created_by_user=self.admin_user
        )
        
        # Initially no reads
        self.assertEqual(notification.read_count, 0)
        self.assertEqual(notification.read_rate, 0)
        
        # Mark as read by user
        NotificationRead.objects.create(
            notification=notification,
            user=self.user
        )
        
        # Check read count
        self.assertEqual(notification.read_count, 1)


class NotificationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='testuser',
            password='testpass123',
            role='user'
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='adminuser',
            password='adminpass123',
            role='admin'
        )
        
        self.notification = Notification.objects.create(
            title='Test Notification',
            notification_type='announcement',
            priority='medium',
            target_audience='all_users',
            message='This is a test notification',
            created_by='admin',
            created_by_user=self.admin_user
        )
        
    def test_user_can_view_notifications(self):
        """Test that users can view their notifications"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-notifications-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_user_cannot_access_admin_endpoints(self):
        """Test that regular users cannot access admin endpoints"""
        self.client.force_authenticate(user=self.user)
        url = reverse('admin-notifications-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_mark_notification_as_read(self):
        """Test marking notification as read"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-notifications-mark-as-read')
        data = {
            'notification_ids': [str(self.notification.id)]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            NotificationRead.objects.filter(
                notification=self.notification,
                user=self.user
            ).exists()
        )
