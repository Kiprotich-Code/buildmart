from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message, ProductQuestion, ProductAnswer, AnswerHelpful
from products.models import Product

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for chat participants"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name']
        read_only_fields = fields


class ProductBasicSerializer(serializers.ModelSerializer):
    """Basic product serializer for chat context"""
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'images']
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender = UserBasicSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'sender_id', 'message_type', 
            'content', 'file_url', 'is_read', 'is_edited', 
            'edited_at', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'is_edited', 'edited_at', 'created_at']
    
    def create(self, validated_data):
        # Set sender from request user if not provided
        if 'sender_id' not in validated_data:
            validated_data['sender'] = self.context['request'].user
        else:
            validated_data['sender_id'] = validated_data.pop('sender_id')
        return super().create(validated_data)


class ChatSerializer(serializers.ModelSerializer):
    """Serializer for chat conversations"""
    buyer = UserBasicSerializer(read_only=True)
    seller = UserBasicSerializer(read_only=True)
    product = ProductBasicSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = [
            'id', 'buyer', 'seller', 'product', 'last_message_at',
            'is_active', 'created_at', 'last_message', 'unread_count',
            'other_participant'
        ]
        read_only_fields = fields
    
    def get_last_message(self, obj):
        """Get the last message in the chat"""
        last_message = obj.messages.last()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content,
                'message_type': last_message.message_type,
                'sender_email': last_message.sender.email,
                'created_at': last_message.created_at,
                'is_read': last_message.is_read
            }
        return None
    
    def get_unread_count(self, obj):
        """Get count of unread messages for current user"""
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()
    
    def get_other_participant(self, obj):
        """Get the other participant in the chat (not the current user)"""
        user = self.context['request'].user
        if obj.buyer == user:
            return UserBasicSerializer(obj.seller).data
        return UserBasicSerializer(obj.buyer).data


class ChatCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new chats"""
    product_id = serializers.UUIDField()
    
    class Meta:
        model = Chat
        fields = ['product_id']
    
    def validate_product_id(self, value):
        """Validate that the product exists and is active"""
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")
        
        # Check if user is trying to chat with themselves
        if product.seller == self.context['request'].user:
            raise serializers.ValidationError("You cannot start a chat with yourself")
        
        return value
    
    def create(self, validated_data):
        """Create a new chat or return existing one"""
        product = Product.objects.get(id=validated_data['product_id'])
        buyer = self.context['request'].user
        seller = product.seller
        
        # Get or create chat
        chat, created = Chat.objects.get_or_create(
            buyer=buyer,
            seller=seller,
            product=product,
            defaults={'is_active': True}
        )
        
        # If chat exists but was inactive, reactivate it
        if not created and not chat.is_active:
            chat.is_active = True
            chat.save()
        
        return chat


class MessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating message read status"""
    
    class Meta:
        model = Message
        fields = ['is_read']


# Q&A Serializers

class ProductAnswerSerializer(serializers.ModelSerializer):
    """Serializer for product answers"""
    user = UserBasicSerializer(read_only=True)
    user_name = serializers.SerializerMethodField()
    is_helpful = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductAnswer
        fields = [
            'id', 'user', 'user_name', 'answer', 'is_seller_answer', 
            'is_verified', 'helpful_count', 'is_helpful', 'time_since', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'is_seller_answer', 'is_verified', 'helpful_count', 'created_at']
    
    def get_user_name(self, obj):
        """Get display name for the user"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        elif obj.user.username:
            return obj.user.username
        else:
            return obj.user.email.split('@')[0]
    
    def get_is_helpful(self, obj):
        """Check if current user marked this answer as helpful"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnswerHelpful.objects.filter(answer=obj, user=request.user).exists()
        return False
    
    def get_time_since(self, obj):
        """Get human-readable time since answer was posted"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class ProductQuestionSerializer(serializers.ModelSerializer):
    """Serializer for product questions"""
    user = UserBasicSerializer(read_only=True)
    user_name = serializers.SerializerMethodField()
    answers = ProductAnswerSerializer(many=True, read_only=True)
    answer_count = serializers.ReadOnlyField()
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductQuestion
        fields = [
            'id', 'user', 'user_name', 'question', 'is_answered', 
            'answer_count', 'answers', 'time_since', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'is_answered', 'answer_count', 'created_at']
    
    def get_user_name(self, obj):
        """Get display name for the user"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        elif obj.user.username:
            return obj.user.username
        else:
            return obj.user.email.split('@')[0]
    
    def get_time_since(self, obj):
        """Get human-readable time since question was asked"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class ProductQuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating product questions"""
    
    class Meta:
        model = ProductQuestion
        fields = ['product', 'question']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProductAnswerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating product answers"""
    
    class Meta:
        model = ProductAnswer
        fields = ['question', 'answer']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
