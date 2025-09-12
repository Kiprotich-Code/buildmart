from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class RecentActivity(models.Model):
    ACTION_TYPES = [
        # Admin activities
        ('user_registration', 'User Registration'),
        ('payment_approved', 'Payment Approved'),
        ('boost_activated', 'Boost Activated'),
        ('product_flagged', 'Product Flagged'),
        ('product_approved', 'Product Approved'),
        ('user_suspended', 'User Suspended'),
        ('user_reactivated', 'User Reactivated'),
        ('seller_verified', 'Seller Verified'),
        ('payment_processed', 'Payment Processed'),
        
        # Buyer activities (product views)
        ('product_viewed', 'Product Viewed'),
        ('material_viewed', 'Material Viewed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    related_object_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID of related object (product, payment, etc.)")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional data like product name, amount, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recent_activities'
        ordering = ['-created_at']
        verbose_name = 'Recent Activity'
        verbose_name_plural = 'Recent Activities'
    
    def __str__(self):
        return f"{self.action_type}: {self.message[:50]}"
    
    @classmethod
    def log_activity(cls, action_type, message, user=None, related_object_id=None, metadata=None):
        """
        Convenience method to log activities
        """
        return cls.objects.create(
            action_type=action_type,
            message=message,
            user=user,
            related_object_id=related_object_id,
            metadata=metadata or {}
        )
