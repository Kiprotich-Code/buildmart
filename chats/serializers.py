from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message
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
