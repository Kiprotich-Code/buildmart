from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max, Prefetch, Count, Avg, Case, When, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate

from .models import Chat, Message
from .serializers import (
    ChatSerializer, 
    ChatCreateSerializer, 
    MessageSerializer,
    MessageUpdateSerializer
)
from products.models import Product

User = get_user_model()
channel_layer = get_channel_layer()


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
        
        # Notify seller about new chat via WebSocket
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'user_{chat.seller.id}',
                {
                    'type': 'chat_created_notification',
                    'chat_id': str(chat.id),
                    'participant_name': chat.buyer.get_full_name() or chat.buyer.username,
                    'product_name': chat.product.name if chat.product else 'General Chat'
                }
            )
        
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
        
        # Send real-time notification via WebSocket
        if channel_layer:
            # Notify chat participants
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat.id}',
                {
                    'type': 'chat_message',
                    'message': serializer.data
                }
            )
            
            # Notify other user for unread count update
            other_user = chat.seller if chat.buyer == request.user else chat.buyer
            async_to_sync(channel_layer.group_send)(
                f'user_{other_user.id}',
                {
                    'type': 'new_message_notification',
                    'chat_id': str(chat.id),
                    'message_id': str(message.id),
                    'sender_name': request.user.get_full_name() or request.user.username,
                    'content_preview': message.content[:50] + '...' if len(message.content) > 50 else message.content
                }
            )
        
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
        
        return Response({
            'unread_count': unread_count
        })

    # =============================================================================
    # ADMIN CHAT MONITORING ENDPOINTS
    # =============================================================================
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def admin_all_chats(self, request):
        """
        Get all chats for admin monitoring.
        GET /api/chats/chats/admin_all_chats/
        
        Query Parameters:
        - page: Page number
        - page_size: Number of chats per page (default: 20)
        - status: 'active', 'archived', 'all' (default: 'all')
        - is_flagged: true/false to filter flagged chats
        - search: Search in buyer/seller emails or product names
        - date_from: Filter chats created from this date (YYYY-MM-DD)
        - date_to: Filter chats created to this date (YYYY-MM-DD)
        """
        # Get query parameters
        status_filter = request.query_params.get('status', 'all')
        is_flagged = request.query_params.get('is_flagged')
        search_term = request.query_params.get('search', '').strip()
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        page_size = int(request.query_params.get('page_size', 20))
        
        # Base queryset with all chats - don't use self.get_queryset() for admin
        queryset = Chat.objects.select_related(
            'buyer', 'seller', 'product', 'product__category'
        ).prefetch_related(
            'messages__sender'
        ).annotate(
            message_count=Count('messages'),
            unread_count=Count('messages', filter=Q(messages__is_read=False))
        )
        
        # Apply status filter
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'archived':
            queryset = queryset.filter(is_active=False)
        # 'all' includes both active and inactive
        
        # Apply flagged filter
        if is_flagged == 'true':
            queryset = queryset.filter(is_flagged=True)
        elif is_flagged == 'false':
            queryset = queryset.filter(is_flagged=False)
        
        # Apply search filter
        if search_term:
            queryset = queryset.filter(
                Q(buyer__email__icontains=search_term) |
                Q(seller__email__icontains=search_term) |
                Q(buyer__first_name__icontains=search_term) |
                Q(buyer__last_name__icontains=search_term) |
                Q(seller__first_name__icontains=search_term) |
                Q(seller__last_name__icontains=search_term) |
                Q(product__name__icontains=search_term)
            )
        
        # Apply date filters
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Order by latest activity
        queryset = queryset.order_by('-last_message_at', '-created_at')
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Create admin-specific serialized data
            admin_chats = []
            for chat in page:
                # Get last message
                last_message = chat.messages.order_by('-created_at').first()
                last_message_data = None
                if last_message:
                    last_message_data = {
                        'content': last_message.content,
                        'sender_email': last_message.sender.email,
                        'created_at': last_message.created_at
                    }
                
                admin_chat_data = {
                    'id': str(chat.id),
                    'buyer': {
                        'id': str(chat.buyer.id),
                        'first_name': chat.buyer.first_name,
                        'last_name': chat.buyer.last_name,
                        'email': chat.buyer.email,
                        'role': 'buyer'
                    },
                    'seller': {
                        'id': str(chat.seller.id),
                        'first_name': chat.seller.first_name,
                        'last_name': chat.seller.last_name,
                        'email': chat.seller.email,
                        'role': 'seller'
                    },
                    'product': {
                        'id': str(chat.product.id),
                        'name': chat.product.name,
                        'price': str(chat.product.price),
                        'images': chat.product.images or []
                    },
                    'created_at': chat.created_at,
                    'last_message_at': chat.last_message_at or chat.created_at,
                    'last_message': last_message_data,
                    'message_count': chat.message_count,
                    'unread_count': chat.unread_count,
                    'is_active': chat.is_active,
                    'is_flagged': chat.is_flagged,
                    'flag_reason': chat.flag_reason,
                    'status': 'active' if chat.is_active else 'archived'
                }
                admin_chats.append(admin_chat_data)
            
            return self.get_paginated_response(admin_chats)
        
        # If no pagination, return all results
        admin_chats = []
        for chat in queryset:
            # Get last message
            last_message = chat.messages.order_by('-created_at').first()
            last_message_data = None
            if last_message:
                last_message_data = {
                    'content': last_message.content,
                    'sender_email': last_message.sender.email,
                    'created_at': last_message.created_at
                }
            
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def admin_all_chats(self, request):
        """
        Get all chats for admin monitoring - SIMPLIFIED VERSION.
        GET /api/chats/chats/admin_all_chats/
        """
        try:
            # Get chats with valid relationships
            chats = Chat.objects.select_related('buyer', 'seller', 'product').filter(
                buyer__isnull=False,
                seller__isnull=False,
                product__isnull=False
            )[:10]
            
            results = []
            for chat in chats:
                try:
                    results.append({
                        'id': str(chat.id),
                        'buyer': {
                            'id': str(chat.buyer.id),
                            'first_name': chat.buyer.first_name or '',
                            'last_name': chat.buyer.last_name or '',
                            'email': chat.buyer.email,
                            'role': 'buyer'
                        },
                        'seller': {
                            'id': str(chat.seller.id),
                            'first_name': chat.seller.first_name or '',
                            'last_name': chat.seller.last_name or '',
                            'email': chat.seller.email,
                            'role': 'seller'
                        },
                        'product': {
                            'id': str(chat.product.id),
                            'name': chat.product.name,
                            'price': str(chat.product.price),
                            'images': chat.product.images or []
                        },
                        'created_at': chat.created_at,
                        'last_message_at': chat.last_message_at or chat.created_at,
                        'message_count': chat.messages.count(),
                        'unread_count': 0,  # Simplified
                        'is_active': chat.is_active,
                        'is_flagged': getattr(chat, 'is_flagged', False),
                        'flag_reason': getattr(chat, 'flag_reason', None),
                        'status': 'active' if chat.is_active else 'archived'
                    })
                except Exception as chat_error:
                    print(f"Error processing chat {chat.id}: {chat_error}")
                    continue
            
            return Response({
                'count': Chat.objects.count(),
                'results': results
            })
            
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Error in admin_all_chats'
            }, status=500)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def admin_statistics(self, request):
        """
        Get chat statistics for admin dashboard.
        GET /api/chats/chats/admin_statistics/
        """
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        
        # Basic counts
        total_chats = Chat.objects.count()
        active_chats = Chat.objects.filter(is_active=True).count()
        archived_chats = Chat.objects.filter(is_active=False).count()
        flagged_chats = Chat.objects.filter(is_flagged=True).count()
        
        # Total messages
        total_messages = Message.objects.count()
        
        # Daily new chats
        daily_new_chats = Chat.objects.filter(
            created_at__date=today
        ).count()
        
        # Weekly growth calculation
        week_ago_total = Chat.objects.filter(
            created_at__date__lt=week_ago
        ).count()
        
        if week_ago_total > 0:
            current_week_chats = total_chats - week_ago_total
            weekly_growth = (current_week_chats / week_ago_total) * 100
        else:
            weekly_growth = 0
        
        # Average response time calculation (simplified)
        # This is a basic implementation - you might want to make it more sophisticated
        avg_response_time = 300  # Default 5 minutes in seconds
        
        # You could calculate real response time by analyzing message timestamps
        # between different senders in conversations
        
        statistics = {
            'total_chats': total_chats,
            'active_chats': active_chats,
            'archived_chats': archived_chats,
            'flagged_chats': flagged_chats,
            'total_messages': total_messages,
            'average_response_time': avg_response_time,
            'daily_new_chats': daily_new_chats,
            'weekly_growth': round(weekly_growth, 1)
        }
        
        return Response(statistics)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def admin_chat_messages(self, request, pk=None):
        """
        Get all messages for a specific chat (admin view).
        GET /api/chats/chats/{chat_id}/admin_chat_messages/
        """
        # Admin can access any chat - don't use get_object() which applies filters
        chat = get_object_or_404(Chat, id=pk)
        messages = chat.messages.select_related('sender').order_by('created_at')
        
        admin_messages = []
        for message in messages:
            admin_message_data = {
                'id': str(message.id),
                'content': message.content,
                'message_type': message.message_type,
                'sender': {
                    'id': str(message.sender.id),
                    'first_name': message.sender.first_name,
                    'last_name': message.sender.last_name,
                    'email': message.sender.email,
                    'role': 'buyer' if message.sender == chat.buyer else 'seller'
                },
                'created_at': message.created_at,
                'is_read': message.is_read,
                'file_url': message.file_url
            }
            admin_messages.append(admin_message_data)
        
        return Response(admin_messages)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def admin_flag_chat(self, request, pk=None):
        """
        Flag a chat for admin review.
        POST /api/chats/chats/{chat_id}/admin_flag_chat/
        
        Body: {
            "reason": "Reason for flagging"
        }
        """
        chat = get_object_or_404(Chat, id=pk)
        reason = request.data.get('reason', 'Admin review required')
        
        chat.is_flagged = True
        chat.flag_reason = reason
        chat.save(update_fields=['is_flagged', 'flag_reason'])
        
        return Response({
            'message': 'Chat flagged successfully',
            'chat_id': str(chat.id),
            'reason': reason
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def admin_unflag_chat(self, request, pk=None):
        """
        Remove flag from a chat.
        POST /api/chats/chats/{chat_id}/admin_unflag_chat/
        """
        chat = get_object_or_404(Chat, id=pk)
        
        chat.is_flagged = False
        chat.flag_reason = None
        chat.save(update_fields=['is_flagged', 'flag_reason'])
        
        return Response({
            'message': 'Chat unflagged successfully',
            'chat_id': str(chat.id)
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def admin_archive_chat(self, request, pk=None):
        """
        Archive a chat (set is_active to False).
        POST /api/chats/chats/{chat_id}/admin_archive_chat/
        """
        chat = get_object_or_404(Chat, id=pk)
        
        chat.is_active = False
        chat.save(update_fields=['is_active'])
        
        return Response({
            'message': 'Chat archived successfully',
            'chat_id': str(chat.id)
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def admin_restore_chat(self, request, pk=None):
        """
        Restore an archived chat (set is_active to True).
        POST /api/chats/chats/{chat_id}/admin_restore_chat/
        """
        chat = get_object_or_404(Chat, id=pk)
        
        chat.is_active = True
        chat.save(update_fields=['is_active'])
        
        return Response({
            'message': 'Chat restored successfully',
            'chat_id': str(chat.id)
        })
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAdminUser])
    def admin_delete_chat(self, request, pk=None):
        """
        Permanently delete a chat and all its messages.
        DELETE /api/chats/chats/{chat_id}/admin_delete_chat/
        """
        chat = get_object_or_404(Chat, id=pk)
        chat_id = str(chat.id)
        
        # Delete all messages first
        chat.messages.all().delete()
        
        # Delete the chat
        chat.delete()
        
        return Response({
            'message': 'Chat deleted permanently',
            'chat_id': chat_id
        }, status=status.HTTP_204_NO_CONTENT)


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
