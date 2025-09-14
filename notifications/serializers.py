from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, NotificationRead, Contact

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for notification display"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role']


class NotificationReadSerializer(serializers.ModelSerializer):
    """Serializer for notification read tracking"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = NotificationRead
        fields = ['id', 'user', 'read_at', 'clicked', 'clicked_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Main notification serializer for admin operations"""
    specific_users = UserBasicSerializer(many=True, read_only=True)
    specific_user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    created_by_user = UserBasicSerializer(read_only=True)
    
    # Read-only statistics
    total_recipients = serializers.ReadOnlyField()
    read_count = serializers.ReadOnlyField()
    read_rate = serializers.ReadOnlyField()
    click_count = serializers.ReadOnlyField()
    click_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'notification_type', 'priority', 'target_audience',
            'specific_users', 'specific_user_ids', 'message', 'action_buttons',
            'created_by', 'created_by_user', 'created_at', 'updated_at',
            'is_active', 'scheduled_for', 'total_recipients', 'read_count',
            'read_rate', 'click_count', 'click_rate'
        ]
        
    def validate_action_buttons(self, value):
        """Validate action buttons format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Action buttons must be a list")
        
        for button in value:
            if not isinstance(button, dict):
                raise serializers.ValidationError("Each action button must be an object")
            if 'text' not in button or 'url' not in button:
                raise serializers.ValidationError("Each action button must have 'text' and 'url' fields")
        
        return value
    
    def validate(self, data):
        """Validate notification data"""
        # If target_audience is specific_users, specific_user_ids is required
        if data.get('target_audience') == 'specific_users':
            specific_user_ids = data.get('specific_user_ids', [])
            if not specific_user_ids:
                raise serializers.ValidationError({
                    'specific_user_ids': 'This field is required when target_audience is specific_users'
                })
        
        return data
    
    def create(self, validated_data):
        """Create notification with specific users"""
        specific_user_ids = validated_data.pop('specific_user_ids', [])
        notification = Notification.objects.create(**validated_data)
        
        if specific_user_ids:
            users = User.objects.filter(id__in=specific_user_ids)
            notification.specific_users.set(users)
        
        return notification
    
    def update(self, instance, validated_data):
        """Update notification with specific users"""
        specific_user_ids = validated_data.pop('specific_user_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if specific_user_ids is not None:
            users = User.objects.filter(id__in=specific_user_ids)
            instance.specific_users.set(users)
        
        return instance


class UserNotificationSerializer(serializers.ModelSerializer):
    """Simplified notification serializer for user view"""
    is_read = serializers.SerializerMethodField()
    read_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'notification_type', 'priority', 'message',
            'action_buttons', 'created_at', 'is_read', 'read_at'
        ]
    
    def get_is_read(self, obj):
        """Check if current user has read this notification"""
        user = self.context['request'].user
        if user.is_authenticated:
            return NotificationRead.objects.filter(
                notification=obj, 
                user=user
            ).exists()
        return False
    
    def get_read_at(self, obj):
        """Get when current user read this notification"""
        user = self.context['request'].user
        if user.is_authenticated:
            read_record = NotificationRead.objects.filter(
                notification=obj, 
                user=user
            ).first()
            return read_record.read_at if read_record else None
        return None


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_sent = serializers.IntegerField()
    total_read = serializers.IntegerField()
    total_clicked = serializers.IntegerField()
    total_pending = serializers.IntegerField()
    overall_read_rate = serializers.FloatField()
    overall_click_rate = serializers.FloatField()
    
    # Breakdown by type
    by_type = serializers.DictField()
    by_priority = serializers.DictField()
    by_target_audience = serializers.DictField()


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    clicked = serializers.BooleanField(default=False, required=False)


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact form submissions"""
    
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'phone', 'subject', 'category', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_email(self, value):
        """Validate email format"""
        if not value:
            raise serializers.ValidationError("Email is required.")
        return value
    
    def validate_name(self, value):
        """Validate name field"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.strip()
    
    def validate_subject(self, value):
        """Validate subject field"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Subject must be at least 5 characters long.")
        return value.strip()
    
    def validate_message(self, value):
        """Validate message field"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value.strip()
