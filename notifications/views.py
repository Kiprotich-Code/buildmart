from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Notification, NotificationRead, Contact
from .serializers import (
    NotificationSerializer, 
    UserNotificationSerializer, 
    NotificationStatsSerializer,
    MarkAsReadSerializer,
    NotificationReadSerializer,
    ContactSerializer
)
from accounts.permissions import IsAdminUser

User = get_user_model()


class NotificationViewSet(viewsets.ModelViewSet):
    """Admin notification management viewset"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = []  # Temporarily disable auth for testing
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'target_audience', 'is_active', 'created_by']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set the created_by_user to current user"""
        serializer.save(created_by_user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics for admin dashboard"""
        notifications = Notification.objects.all()
        
        # Basic stats
        total_sent = notifications.count()
        total_reads = NotificationRead.objects.count()
        total_clicks = NotificationRead.objects.filter(clicked=True).count()
        total_pending = notifications.filter(is_active=True, scheduled_for__gt=timezone.now()).count()
        
        # Calculate overall rates
        total_recipients = sum(n.total_recipients for n in notifications)
        overall_read_rate = round((total_reads / total_recipients) * 100, 2) if total_recipients > 0 else 0
        overall_click_rate = round((total_clicks / total_recipients) * 100, 2) if total_recipients > 0 else 0
        
        # Breakdown by type
        by_type = {}
        for choice in Notification.TYPE_CHOICES:
            type_notifications = notifications.filter(notification_type=choice[0])
            by_type[choice[0]] = {
                'count': type_notifications.count(),
                'read_rate': sum(n.read_rate for n in type_notifications) / max(type_notifications.count(), 1)
            }
        
        # Breakdown by priority
        by_priority = {}
        for choice in Notification.PRIORITY_CHOICES:
            priority_notifications = notifications.filter(priority=choice[0])
            by_priority[choice[0]] = {
                'count': priority_notifications.count(),
                'read_rate': sum(n.read_rate for n in priority_notifications) / max(priority_notifications.count(), 1)
            }
        
        # Breakdown by target audience
        by_target_audience = {}
        for choice in Notification.TARGET_AUDIENCE_CHOICES:
            audience_notifications = notifications.filter(target_audience=choice[0])
            by_target_audience[choice[0]] = {
                'count': audience_notifications.count(),
                'read_rate': sum(n.read_rate for n in audience_notifications) / max(audience_notifications.count(), 1)
            }
        
        stats_data = {
            'total_sent': total_sent,
            'total_read': total_reads,
            'total_clicked': total_clicks,
            'total_pending': total_pending,
            'overall_read_rate': overall_read_rate,
            'overall_click_rate': overall_click_rate,
            'by_type': by_type,
            'by_priority': by_priority,
            'by_target_audience': by_target_audience
        }
        
        serializer = NotificationStatsSerializer(data=stats_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def readers(self, request, pk=None):
        """Get list of users who have read this notification"""
        notification = self.get_object()
        reads = NotificationRead.objects.filter(notification=notification).select_related('user')
        serializer = NotificationReadSerializer(reads, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a notification"""
        original = self.get_object()
        
        # Create a copy
        duplicate_data = {
            'title': f"Copy of {original.title}",
            'notification_type': original.notification_type,
            'priority': original.priority,
            'target_audience': original.target_audience,
            'message': original.message,
            'action_buttons': original.action_buttons,
            'created_by': original.created_by,
            'is_active': False  # Make inactive by default
        }
        
        serializer = self.get_serializer(data=duplicate_data)
        serializer.is_valid(raise_exception=True)
        duplicate = serializer.save(created_by_user=request.user)
        
        # Copy specific users if applicable
        if original.target_audience == 'specific_users':
            duplicate.specific_users.set(original.specific_users.all())
        
        return Response(self.get_serializer(duplicate).data, status=status.HTTP_201_CREATED)


class UserNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """User notification viewing viewset"""
    serializer_class = UserNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]  # Require authentication
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['notification_type', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get notifications for current user based on target audience"""
        user = self.request.user
        if not user.is_authenticated:
            return Notification.objects.none()
            
        # Filter notifications based on target audience
        notifications = Notification.objects.filter(is_active=True)
        
        # Build the filter conditions
        conditions = Q(target_audience='all_users')
        
        if hasattr(user, 'role'):
            if user.role == 'seller':
                conditions |= Q(target_audience='sellers')
            elif user.role == 'user':
                conditions |= Q(target_audience='buyers')
            elif user.role == 'admin':
                conditions |= Q(target_audience='admins')
        
        # Add specific users condition
        conditions |= Q(target_audience='specific_users', specific_users=user)
        
        user_notifications = notifications.filter(conditions).distinct()
        print(f"UserNotificationViewSet - Found {user_notifications.count()} notifications for user {user.email}")
        
        return user_notifications
    
    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """Mark notifications as read"""
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data.get('notification_ids', [])
        clicked = serializer.validated_data.get('clicked', False)
        
        # If no specific IDs provided, mark all user notifications as read
        if not notification_ids:
            user_notifications = self.get_queryset()
            notification_ids = list(user_notifications.values_list('id', flat=True))
        
        # Get notifications accessible to this user
        accessible_notifications = self.get_queryset().filter(id__in=notification_ids)
        
        marked_count = 0
        for notification in accessible_notifications:
            read_record, created = NotificationRead.objects.get_or_create(
                notification=notification,
                user=request.user,
                defaults={'clicked': clicked}
            )
            
            # Update clicked status if needed
            if not created and clicked and not read_record.clicked:
                read_record.clicked = True
                read_record.clicked_at = timezone.now()
                read_record.save()
            
            if created:
                marked_count += 1
        
        return Response({
            'message': f'Marked {marked_count} notifications as read',
            'marked_count': marked_count
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for current user"""
        user_notifications = self.get_queryset()
        read_notification_ids = NotificationRead.objects.filter(
            user=request.user,
            notification__in=user_notifications
        ).values_list('notification_id', flat=True)
        
        unread_count = user_notifications.exclude(id__in=read_notification_ids).count()
        
        return Response({'unread_count': unread_count})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get only unread notifications for current user"""
        user_notifications = self.get_queryset()
        read_notification_ids = NotificationRead.objects.filter(
            user=request.user,
            notification__in=user_notifications
        ).values_list('notification_id', flat=True)
        
        unread_notifications = user_notifications.exclude(id__in=read_notification_ids)
        
        page = self.paginate_queryset(unread_notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)


class ContactViewSet(viewsets.ModelViewSet):
    """Contact form submission viewset - No authentication required"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]  # No authentication required
    http_method_names = ['post']  # Only allow POST requests
    
    def perform_create(self, serializer):
        """Save contact and send email notification"""
        contact = serializer.save()
        
        # Send email notification to admin
        try:
            self.send_contact_email(contact)
            contact.email_sent = True
            contact.email_sent_at = timezone.now()
            contact.save()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to send contact email: {str(e)}")
        
        return contact
    
    def send_contact_email(self, contact):
        """Send email notification to admin about new contact form submission"""
        subject = f"New Contact Form Submission: {contact.subject}"
        
        # Format the email message
        message = f"""
New contact form submission received:

Name: {contact.name}
Email: {contact.email}
Phone: {contact.phone or 'Not provided'}
Category: {contact.get_category_display()}
Subject: {contact.subject}

Message:
{contact.message}

Submitted at: {contact.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Contact ID: {contact.id}
        """
        
        # Send email to admin
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
    
    def create(self, request, *args, **kwargs):
        """Override create to provide custom response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = self.perform_create(serializer)
        
        return Response({
            'id': contact.id,
            'message': 'Your message has been sent successfully! We will get back to you soon.',
            'success': True
        }, status=status.HTTP_201_CREATED)
