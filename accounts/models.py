from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('seller', 'Seller'), 
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_email_verified = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'custom_users'
        
    def __str__(self):
        return self.email
        
    @property
    def is_seller(self):
        return self.role == 'seller'
        
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
        
    @property
    def is_user(self):
        return self.role == 'user'


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_profile')
        ]

    def __str__(self):
        return f"{self.full_name} ({self.user.role})"


class Seller(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='seller')
    shop_name = models.CharField(max_length=255)
    shop_description = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, default="0")  # Required phone number field with default
    business_license = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    union_membership_number = models.CharField(max_length=100, blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    trial_end_date = models.DateTimeField()
    subscription_active = models.BooleanField(default=True)
    subscription_end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sellers'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_seller')
        ]

    def __str__(self):
        return self.shop_name
    
    @property
    def is_verified(self):
        return self.verification_status == 'verified'


# Signal to create Profile only for regular users and admins
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role != 'seller':
        # Only create Profile for users and admins, not for sellers
        Profile.objects.create(
            user=instance,
            full_name=f"{instance.first_name} {instance.last_name}".strip() or instance.email
        )