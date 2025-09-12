from rest_framework import serializers
from .models import RecentActivity
from accounts.serializers import UserSerializer

class RecentActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_type_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = RecentActivity
        fields = [
            'id',
            'action_type',
            'action_display',
            'message',
            'user',
            'related_object_id',
            'metadata',
            'created_at',
            'time_ago'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_time_ago(self, obj):
        """Return a human-readable time ago string"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return obj.created_at.strftime('%b %d, %Y')

class AdminActivitySerializer(RecentActivitySerializer):
    """Serializer for admin activities with additional fields"""
    pass

class BuyerActivitySerializer(serializers.ModelSerializer):
    """Simplified serializer for buyer product view activities"""
    time_ago = serializers.SerializerMethodField()
    product_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RecentActivity
        fields = [
            'id',
            'action_type',
            'message',
            'product_info',
            'created_at',
            'time_ago'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_time_ago(self, obj):
        """Return a human-readable time ago string"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return obj.created_at.strftime('%b %d, %Y')
    
    def get_product_info(self, obj):
        """Extract product information from metadata"""
        metadata = obj.metadata or {}
        return {
            'name': metadata.get('product_name', ''),
            'price': metadata.get('price', ''),
            'category': metadata.get('category', ''),
            'id': obj.related_object_id
        }
