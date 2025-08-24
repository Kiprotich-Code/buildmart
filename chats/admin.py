from django.contrib import admin
from .models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'seller', 'product', 'last_message_at', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'last_message_at']
    search_fields = ['buyer__email', 'seller__email', 'product__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['buyer', 'seller', 'product']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer', 'seller', 'product')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'sender', 'message_type', 'content_preview', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'is_edited', 'created_at']
    search_fields = ['sender__email', 'content', 'chat__id']
    readonly_fields = ['id', 'created_at', 'edited_at']
    raw_id_fields = ['chat', 'sender']
    
    def content_preview(self, obj):
        """Show a preview of the message content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('chat', 'sender')
