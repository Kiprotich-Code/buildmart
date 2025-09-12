from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

User = get_user_model()


class Report(models.Model):
    """
    Model for handling user reports on listings, sellers, messages, etc.
    """
    REPORT_TYPES = [
        ('listing', 'Listing'),
        ('seller', 'Seller'),
        ('message', 'Message'),
        ('review', 'Review'),
    ]
    
    REPORT_REASONS = [
        ('fake_listing', 'Fake Listing'),
        ('fraud', 'Fraud'),
        ('harassment', 'Harassment'),
        ('spam', 'Spam'),
        ('inappropriate_content', 'Inappropriate Content'),
        ('quality_issues', 'Quality Issues'),
        ('fake_reviews', 'Fake Reviews'),
        ('scam', 'Scam'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, unique=True, editable=False)
    type = models.CharField(max_length=20, choices=REPORT_TYPES)
    
    # Generic foreign key to handle different types of reported items
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    reported_item = GenericForeignKey('content_type', 'object_id')
    
    # Reporter information
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    
    # Reported user (seller, message sender, etc.)
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reports', null=True, blank=True)
    
    # Report details
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Evidence
    evidence_urls = models.JSONField(default=list, blank=True, help_text="URLs to evidence files/images")
    
    # Admin handling
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin use")
    resolution = models.TextField(blank=True, null=True, help_text="Description of how the report was resolved")
    assigned_admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_reports',
        limit_choices_to={'role': 'admin'}
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['reporter']),
            models.Index(fields=['reported_user']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate custom ID like "rpt_001"
            last_report = Report.objects.order_by('-created_at').first()
            if last_report:
                last_num = int(last_report.id.split('_')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.id = f"rpt_{new_num:03d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Report {self.id}: {self.type} - {self.get_reason_display()}"
    
    @property
    def reported_item_id(self):
        """Return the ID of the reported item"""
        return str(self.object_id)
    
    @property
    def reported_item_title(self):
        """Return a descriptive title for the reported item"""
        if self.reported_item:
            if hasattr(self.reported_item, 'name'):
                return self.reported_item.name
            elif hasattr(self.reported_item, 'shop_name'):
                return self.reported_item.shop_name
            elif hasattr(self.reported_item, 'content'):
                return f"Message: {self.reported_item.content[:50]}..."
            elif hasattr(self.reported_item, 'title'):
                return self.reported_item.title
        return f"{self.type.title()} #{self.object_id}"
    
    @property
    def reporter_name(self):
        """Return reporter's display name"""
        if hasattr(self.reporter, 'profile') and self.reporter.profile.full_name:
            return self.reporter.profile.full_name
        return self.reporter.username or self.reporter.email
    
    @property
    def reporter_email(self):
        """Return reporter's email"""
        return self.reporter.email
    
    @property
    def reported_user_name(self):
        """Return reported user's display name"""
        if not self.reported_user:
            return None
        if hasattr(self.reported_user, 'seller') and hasattr(self.reported_user.seller, 'shop_name'):
            return self.reported_user.seller.shop_name
        elif hasattr(self.reported_user, 'profile') and self.reported_user.profile.full_name:
            return self.reported_user.profile.full_name
        return self.reported_user.username or self.reported_user.email


class Flag(models.Model):
    """
    Model for automated and manual flags on items for moderation
    """
    ITEM_TYPES = [
        ('listing', 'Listing'),
        ('seller', 'Seller'),
        ('review', 'Review'),
        ('user', 'User'),
    ]
    
    FLAG_TYPES = [
        ('automated', 'Automated'),
        ('user_reported', 'User Reported'),
        ('admin_manual', 'Admin Manual'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
        ('escalated', 'Escalated'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, unique=True, editable=False)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    
    # Generic foreign key to handle different types of flagged items
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    flagged_item = GenericForeignKey('content_type', 'object_id')
    
    flag_type = models.CharField(max_length=20, choices=FLAG_TYPES)
    reason = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Who flagged it
    flagged_by = models.CharField(max_length=100, default='System')  # "System", "Community", or admin name
    flagged_by_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_flags'
    )
    
    # Actions taken
    auto_actions_taken = models.JSONField(default=list, blank=True, help_text="List of automated actions taken")
    manual_review_required = models.BooleanField(default=True)
    
    # Admin handling
    admin_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_flags',
        limit_choices_to={'role': 'admin'}
    )
    
    # Timestamps
    flagged_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'flags'
        ordering = ['-flagged_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['item_type', 'status']),
            models.Index(fields=['flag_type']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate custom ID like "flg_001"
            last_flag = Flag.objects.order_by('-flagged_at').first()
            if last_flag:
                last_num = int(last_flag.id.split('_')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.id = f"flg_{new_num:03d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Flag {self.id}: {self.item_type} - {self.get_severity_display()}"
    
    @property
    def item_id(self):
        """Return the ID of the flagged item"""
        return str(self.object_id)
    
    @property
    def item_title(self):
        """Return a descriptive title for the flagged item"""
        if self.flagged_item:
            if hasattr(self.flagged_item, 'name'):
                return self.flagged_item.name
            elif hasattr(self.flagged_item, 'shop_name'):
                return self.flagged_item.shop_name
            elif hasattr(self.flagged_item, 'title'):
                return self.flagged_item.title
            elif hasattr(self.flagged_item, 'content'):
                return f"Review: {self.flagged_item.content[:50]}..."
        return f"{self.item_type.title()} #{self.object_id}"
