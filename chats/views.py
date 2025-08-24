from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Chat, Message
from .serializers import (
    ChatSerializer, 
    ChatCreateSerializer, 
    MessageSerializer,
    MessageUpdateSerializer
)
from products.models import Product

User = get_user_model()


class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat conversations
    """
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get chats for the current user"""
        user = self.request.user
        return Chat.objects.filter(
            Q(buyer=user) | Q(seller=user),
            is_active=True
        ).select_related(
            'buyer', 'seller', 'product', 'product__category'
        ).prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('sender').order_by('-created_at'),
                to_attr='latest_messages'
            )
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ChatCreateSerializer
        return ChatSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new chat conversation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        chat = serializer.save()
        
        # Return the chat with full details
        chat_serializer = ChatSerializer(chat, context={'request': request})
        return Response(chat_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a specific chat"""
        chat = self.get_object()
        
        # Verify user is participant in this chat
        if request.user not in [chat.buyer, chat.seller]:
            return Response(
                {'error': 'You are not a participant in this chat'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = Message.objects.filter(chat=chat).select_related('sender').order_by('created_at')
        
        # Mark messages as read for current user
        messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a specific chat"""
        chat = self.get_object()
        
        # Verify user is participant in this chat
        if request.user not in [chat.buyer, chat.seller]:
            return Response(
                {'error': 'You are not a participant in this chat'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create message
        data = request.data.copy()
        data['chat'] = chat.id
        
        serializer = MessageSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save(sender=request.user)
        
        # Update chat's last message time
        chat.last_message_at = timezone.now()
        chat.save(update_fields=['last_message_at'])
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        """Mark all messages in chat as read for current user"""
        chat = self.get_object()
        
        # Verify user is participant in this chat
        if request.user not in [chat.buyer, chat.seller]:
            return Response(
                {'error': 'You are not a participant in this chat'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark all unread messages as read
        updated_count = Message.objects.filter(
            chat=chat,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return Response({
            'message': f'{updated_count} messages marked as read'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get total unread message count for current user"""
        user = request.user
        unread_count = Message.objects.filter(
            chat__in=Chat.objects.filter(Q(buyer=user) | Q(seller=user)),
            is_read=False
        ).exclude(sender=user).count()
        
        return Response({'unread_count': unread_count})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get messages for chats where user is a participant"""
        user = self.request.user
        return Message.objects.filter(
            chat__in=Chat.objects.filter(Q(buyer=user) | Q(seller=user))
        ).select_related('sender', 'chat')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['update', 'partial_update'] and 'is_read' in self.request.data:
            return MessageUpdateSerializer
        return MessageSerializer
    
    def update(self, request, *args, **kwargs):
        """Update message (mainly for marking as read)"""
        message = self.get_object()
        
        # Only allow updating read status and only if user is not the sender
        if 'is_read' in request.data and message.sender != request.user:
            message.is_read = request.data['is_read']
            message.save(update_fields=['is_read'])
            
            serializer = self.get_serializer(message)
            return Response(serializer.data)
        
        return Response(
            {'error': 'You can only mark messages as read'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete message (only sender can delete their own messages)"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
