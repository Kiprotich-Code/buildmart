from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
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
        ('pending', 'Pending'),
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


class Dispute(models.Model):
    """
    Model for handling disputes between buyers and sellers.
    Can be created directly or escalated from regular chats.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    RESOLUTION_TYPE_CHOICES = [
        ('mutual', 'Mutual Agreement'),
        ('admin_decision', 'Admin Decision'),
        ('auto_closed', 'Auto Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core participants
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_disputes')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_disputes')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='disputes')
    
    # Dispute details
    title = models.CharField(max_length=255, help_text="Brief description of the dispute")
    description = models.TextField(help_text="Detailed description of the issue")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Admin involvement
    admin_joined = models.BooleanField(default=False)
    admin_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='admin_disputes',
        limit_choices_to={'role': 'admin'}
    )
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_type = models.CharField(max_length=20, choices=RESOLUTION_TYPE_CHOICES, null=True, blank=True)
    resolution_description = models.TextField(blank=True, null=True, help_text="Details of the resolution")
    admin_decision = models.TextField(blank=True, null=True, help_text="Admin's decision if resolved by admin")
    
    # Participant agreement status
    buyer_marked_resolved = models.BooleanField(default=False)
    seller_marked_resolved = models.BooleanField(default=False)
    
    # Escalation from chat
    escalated_from_chat = models.ForeignKey(
        'chats.Chat', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='escalated_disputes'
    )
    
    # Evidence and attachments
    evidence_urls = models.JSONField(default=list, blank=True, help_text="URLs to evidence files/images")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'disputes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['buyer', 'seller']),
            models.Index(fields=['admin_joined']),
            models.Index(fields=['is_resolved']),
        ]
    
    def __str__(self):
        return f"Dispute: {self.title} ({self.buyer.email} vs {self.seller.email})"
    
    @property
    def participants(self):
        """Return list of all participants including admin if joined"""
        participants = [self.buyer, self.seller]
        if self.admin_joined and self.admin_user:
            participants.append(self.admin_user)
        return participants
    
    @property
    def can_be_resolved_mutually(self):
        """Check if dispute can be resolved by mutual agreement"""
        return self.buyer_marked_resolved and self.seller_marked_resolved
    
    def mark_resolved_by_admin(self, admin_user, decision):
        """Mark dispute as resolved by admin with decision"""
        self.is_resolved = True
        self.resolution_type = 'admin_decision'
        self.admin_decision = decision
        self.admin_user = admin_user
        self.resolved_at = timezone.now()
        self.status = 'resolved'
        self.save()
    
    def mark_resolved_mutually(self):
        """Mark dispute as resolved by mutual agreement"""
        if self.can_be_resolved_mutually:
            self.is_resolved = True
            self.resolution_type = 'mutual'
            self.resolved_at = timezone.now()
            self.status = 'resolved'
            self.save()
    
    def join_admin(self, admin_user):
        """Add admin to the dispute"""
        self.admin_joined = True
        self.admin_user = admin_user
        self.save()
        
        # Create system message about admin joining
        DisputeMessage.objects.create(
            dispute=self,
            sender=admin_user,
            message_type='system',
            content=f"Buildmart admin {admin_user.profile.full_name if hasattr(admin_user, 'profile') else admin_user.email} just joined the chat"
        )


class DisputeMessage(models.Model):
    """
    Messages within a dispute - similar to chat messages but with additional features
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System Message'),  # For admin join notifications, etc.
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dispute_messages')
    
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    
    # File attachments
    attachments = models.JSONField(default=list, blank=True, help_text="List of attachment URLs and metadata")
    
    # Message metadata
    is_read_by_buyer = models.BooleanField(default=False)
    is_read_by_seller = models.BooleanField(default=False)
    is_read_by_admin = models.BooleanField(default=False)
    
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dispute_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['dispute', 'created_at']),
            models.Index(fields=['sender']),
        ]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update dispute's last_message_at
        self.dispute.last_message_at = self.created_at
        self.dispute.save(update_fields=['last_message_at'])
    
    def __str__(self):
        return f"Message in {self.dispute.title} by {self.sender.email}"
    
    def mark_read_by_user(self, user):
        """Mark message as read by specific user"""
        if user == self.dispute.buyer:
            self.is_read_by_buyer = True
        elif user == self.dispute.seller:
            self.is_read_by_seller = True
        elif user == self.dispute.admin_user:
            self.is_read_by_admin = True
        self.save()
    
    @property
    def is_read_by_all(self):
        """Check if message is read by all relevant participants"""
        participants_read = []
        if self.dispute.buyer:
            participants_read.append(self.is_read_by_buyer)
        if self.dispute.seller:
            participants_read.append(self.is_read_by_seller)
        if self.dispute.admin_joined and self.dispute.admin_user:
            participants_read.append(self.is_read_by_admin)
        
        return all(participants_read)
