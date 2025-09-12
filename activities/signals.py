from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from products.models import Product
from payments.models import Boost
from .models import RecentActivity

User = get_user_model()

@receiver(post_save, sender=User)
def log_user_registration(sender, instance, created, **kwargs):
    """Log when a new user registers"""
    if created:
        RecentActivity.log_activity(
            action_type='user_registration',
            message=f"New {instance.role} registered: {instance.email}",
            user=instance,
            related_object_id=str(instance.id),
            metadata={
                'email': instance.email,
                'role': instance.role,
                'username': instance.username
            }
        )

@receiver(post_save, sender=Product)
def log_product_approval(sender, instance, created, **kwargs):
    """Log when a product is created or status changes"""
    if created:
        RecentActivity.log_activity(
            action_type='product_approved',
            message=f"New product listed: {instance.name} by {instance.seller.email}",
            user=instance.seller,
            related_object_id=str(instance.id),
            metadata={
                'product_name': instance.name,
                'seller_email': instance.seller.email,
                'category': instance.category.name,
                'price': str(instance.price)
            }
        )

@receiver(post_save, sender=Boost)
def log_boost_activation(sender, instance, created, **kwargs):
    """Log when a boost is activated"""
    if instance.payment_status == 'paid' and instance.is_active:
        # Check if this is a status change to paid (not creation)
        if not created:
            old_instance = Boost.objects.filter(id=instance.id).first()
            if old_instance and old_instance.payment_status != 'paid':
                RecentActivity.log_activity(
                    action_type='boost_activated',
                    message=f"Boost activated for product: {instance.listing.name}",
                    user=instance.user,
                    related_object_id=str(instance.id),
                    metadata={
                        'product_name': instance.listing.name,
                        'plan_name': instance.plan.name,
                        'duration_days': instance.plan.duration_days,
                        'price': str(instance.plan.price)
                    }
                )
        elif created and instance.payment_status == 'paid':
            # New boost created and already paid
            RecentActivity.log_activity(
                action_type='boost_activated',
                message=f"Boost activated for product: {instance.listing.name}",
                user=instance.user,
                related_object_id=str(instance.id),
                metadata={
                    'product_name': instance.listing.name,
                    'plan_name': instance.plan.name,
                    'duration_days': instance.plan.duration_days,
                    'price': str(instance.plan.price)
                }
            )

def log_payment_processed(user, amount, payment_type, transaction_id, metadata=None):
    """Utility function to log payment processing"""
    RecentActivity.log_activity(
        action_type='payment_processed',
        message=f"Payment of ${amount} processed for {payment_type}",
        user=user,
        related_object_id=transaction_id,
        metadata={
            'amount': str(amount),
            'payment_type': payment_type,
            'transaction_id': transaction_id,
            **(metadata or {})
        }
    )

def log_product_view(user, product):
    """Log when a buyer views a product"""
    if user and user.is_authenticated and user.role == 'user':  # Only for buyers
        RecentActivity.log_activity(
            action_type='product_viewed',
            message=f"Product viewed: {product.name}",
            user=user,
            related_object_id=str(product.id),
            metadata={
                'product_name': product.name,
                'seller_email': product.seller.email,
                'category': product.category.name,
                'price': str(product.price)
            }
        )

def log_user_status_change(user, action, admin_user=None):
    """Log user suspension/reactivation"""
    action_type = 'user_suspended' if action == 'suspend' else 'user_reactivated'
    message = f"User {action}ed: {user.email}"
    
    RecentActivity.log_activity(
        action_type=action_type,
        message=message,
        user=admin_user,  # The admin who performed the action
        related_object_id=str(user.id),
        metadata={
            'affected_user_email': user.email,
            'affected_user_role': user.role,
            'admin_email': admin_user.email if admin_user else 'System'
        }
    )

def log_product_flag(product, reason, admin_user=None):
    """Log when a product is flagged"""
    RecentActivity.log_activity(
        action_type='product_flagged',
        message=f"Product flagged: {product.name} - {reason}",
        user=admin_user,
        related_object_id=str(product.id),
        metadata={
            'product_name': product.name,
            'seller_email': product.seller.email,
            'flag_reason': reason,
            'admin_email': admin_user.email if admin_user else 'System'
        }
    )
