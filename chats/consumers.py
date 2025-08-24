import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Chat, Message
from .serializers import MessageSerializer

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for individual chat rooms
    Handles real-time messaging between chat participants
    """
    
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user is a participant in this chat
        is_participant = await self.check_chat_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to chat {self.chat_id}'
        }))
    
    async def disconnect(self, close_code):
        # Leave chat group
        if hasattr(self, 'chat_group_name'):
            await self.channel_layer.group_discard(
                self.chat_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'send_message':
                await self.handle_send_message(text_data_json)
            elif message_type == 'mark_as_read':
                await self.handle_mark_as_read(text_data_json)
            elif message_type == 'typing_indicator':
                await self.handle_typing_indicator(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON data'
            }))
    
    async def handle_send_message(self, data):
        """Handle sending a new message"""
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        file_url = data.get('file_url')
        
        if not content and not file_url:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message content cannot be empty'
            }))
            return
        
        # Create message in database
        message = await self.create_message(content, message_type, file_url)
        
        if message:
            # Serialize message for WebSocket
            serialized_message = await self.serialize_message(message)
            
            # Send message to chat group
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': serialized_message
                }
            )
            
            # Update chat's last_message_at
            await self.update_chat_timestamp()
            
            # Notify other user about new message (for unread count)
            await self.notify_user_new_message(message)
    
    async def handle_mark_as_read(self, data):
        """Handle marking messages as read"""
        count = await self.mark_messages_as_read()
        
        # Notify the chat group about read status update
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'messages_read',
                'user_id': self.user.id,
                'count': count
            }
        )
    
    async def handle_typing_indicator(self, data):
        """Handle typing indicators"""
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator to other participants
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name() or self.user.username,
                'is_typing': is_typing
            }
        )
    
    # WebSocket message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))
    
    async def messages_read(self, event):
        """Send read status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'user_id': event['user_id'],
            'count': event['count']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator back to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))
    
    # Database operations
    @database_sync_to_async
    def check_chat_participant(self):
        """Check if current user is a participant in this chat"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return self.user in [chat.buyer, chat.seller]
        except Chat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def create_message(self, content, message_type, file_url):
        """Create a new message in the database"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                content=content,
                message_type=message_type,
                file_url=file_url
            )
            return message
        except Chat.DoesNotExist:
            return None
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for WebSocket transmission"""
        serializer = MessageSerializer(message)
        return serializer.data
    
    @database_sync_to_async
    def update_chat_timestamp(self):
        """Update the chat's last_message_at timestamp"""
        from django.utils import timezone
        try:
            chat = Chat.objects.get(id=self.chat_id)
            chat.last_message_at = timezone.now()
            chat.save(update_fields=['last_message_at'])
        except Chat.DoesNotExist:
            pass
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark all unread messages as read for current user"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            count = Message.objects.filter(
                chat=chat,
                is_read=False
            ).exclude(sender=self.user).update(is_read=True)
            return count
        except Chat.DoesNotExist:
            return 0
    
    @database_sync_to_async
    def get_other_participant(self):
        """Get the other participant in the chat"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return chat.seller if chat.buyer == self.user else chat.buyer
        except Chat.DoesNotExist:
            return None
    
    async def notify_user_new_message(self, message):
        """Notify the other user about a new message for unread count updates"""
        other_user = await self.get_other_participant()
        if other_user:
            await self.channel_layer.group_send(
                f'user_{other_user.id}',
                {
                    'type': 'new_message_notification',
                    'chat_id': self.chat_id,
                    'message_id': str(message.id),
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'content_preview': message.content[:50] + '...' if len(message.content) > 50 else message.content
                }
            )


class UserConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user-specific notifications
    Handles global notifications like new chat invitations, unread counts, etc.
    """
    
    async def connect(self):
        self.user = self.scope['user']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        
        # Check if user is authenticated and matches the user_id
        if not self.user.is_authenticated or str(self.user.id) != str(self.user_id):
            await self.close()
            return
        
        self.user_group_name = f'user_{self.user_id}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'unread_count': unread_count
        }))
    
    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'get_unread_count':
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON data'
            }))
    
    # WebSocket message handlers
    async def new_message_notification(self, event):
        """Handle new message notifications"""
        await self.send(text_data=json.dumps({
            'type': 'new_message_notification',
            'chat_id': event['chat_id'],
            'message_id': event['message_id'],
            'sender_name': event['sender_name'],
            'content_preview': event['content_preview']
        }))
    
    async def chat_created_notification(self, event):
        """Handle new chat creation notifications"""
        await self.send(text_data=json.dumps({
            'type': 'new_chat',
            'chat_id': event['chat_id'],
            'participant_name': event['participant_name'],
            'product_name': event['product_name']
        }))
    
    # Database operations
    @database_sync_to_async
    def get_unread_count(self):
        """Get total unread message count for user"""
        from django.db.models import Q
        return Message.objects.filter(
            chat__in=Chat.objects.filter(Q(buyer=self.user) | Q(seller=self.user)),
            is_read=False
        ).exclude(sender=self.user).count()
