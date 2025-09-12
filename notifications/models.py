from django.db import models
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()


class Notification(models.Model):
    TYPE_CHOICES = [
        ('announcement', 'Announcement'),
        ('alert', 'Alert'),
        ('reminder', 'Reminder'),
        ('promotion', 'Promotion'),
        ('system', 'System'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    TARGET_AUDIENCE_CHOICES = [
        ('all_users', 'All Users'),
        ('sellers', 'Sellers'),
        ('buyers', 'Buyers'),
        ('admins', 'Admins'),
        ('specific_users', 'Specific Users'),
    ]
    
    CREATED_BY_CHOICES = [
        ('admin', 'Admin'),
        ('marketing_team', 'Marketing Team'),
        ('tech_team', 'Tech Team'),
        ('security_team', 'Security Team'),
        ('support_team', 'Support Team'),
        ('billing_team', 'Billing Team'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES)
    specific_users = models.ManyToManyField(
        User, 
        related_name='targeted_notifications', 
        blank=True,
        help_text="Only used when target_audience is 'specific_users'"
    )
    message = models.TextField()
    
    # Action buttons - stored as JSON
    action_buttons = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of action buttons with 'text' and 'url' keys"
    )
    
    created_by = models.CharField(max_length=20, choices=CREATED_BY_CHOICES)
    created_by_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_notifications'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="For scheduled notifications")
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} ({self.notification_type})"
    
    @property
    def total_recipients(self):
        """Calculate total number of recipients based on target audience"""
        if self.target_audience == 'all_users':
            return User.objects.count()
        elif self.target_audience == 'sellers':
            return User.objects.filter(role='seller').count()
        elif self.target_audience == 'buyers':
            return User.objects.filter(role='user').count()
        elif self.target_audience == 'admins':
            return User.objects.filter(role='admin').count()
        elif self.target_audience == 'specific_users':
            return self.specific_users.count()
        return 0
    
    @property
    def read_count(self):
        """Get number of users who have read this notification"""
        return self.notification_reads.count()
    
    @property
    def read_rate(self):
        """Calculate read rate percentage"""
        total = self.total_recipients
        if total == 0:
            return 0
        return round((self.read_count / total) * 100, 2)
    
    @property
    def click_count(self):
        """Get number of users who have clicked action buttons"""
        return self.notification_reads.filter(clicked=True).count()
    
    @property
    def click_rate(self):
        """Calculate click rate percentage"""
        total = self.total_recipients
        if total == 0:
            return 0
        return round((self.click_count / total) * 100, 2)


class NotificationRead(models.Model):
    """Track which users have read which notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='notification_reads'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_notifications')
    read_at = models.DateTimeField(auto_now_add=True)
    clicked = models.BooleanField(default=False, help_text="Whether user clicked any action button")
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_reads'
        unique_together = ['notification', 'user']
        ordering = ['-read_at']
        
    def __str__(self):
        return f"{self.user.email} read {self.notification.title}"
