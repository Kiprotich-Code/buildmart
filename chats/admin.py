from django.contrib import admin
from .models import Chat, Message, ProductQuestion, ProductAnswer, AnswerHelpful


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


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'user', 'question_preview', 'is_answered', 'answer_count', 'is_active', 'created_at']
    list_filter = ['is_answered', 'is_active', 'created_at']
    search_fields = ['user__email', 'product__name', 'question']
    readonly_fields = ['id', 'answer_count', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'product']
    
    def question_preview(self, obj):
        """Show a preview of the question"""
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')


@admin.register(ProductAnswer)
class ProductAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'user', 'answer_preview', 'is_seller_answer', 'is_verified', 'helpful_count', 'created_at']
    list_filter = ['is_seller_answer', 'is_verified', 'created_at']
    search_fields = ['user__email', 'question__question', 'answer']
    readonly_fields = ['id', 'is_seller_answer', 'created_at', 'updated_at']
    raw_id_fields = ['question', 'user']
    
    def answer_preview(self, obj):
        """Show a preview of the answer"""
        return obj.answer[:50] + '...' if len(obj.answer) > 50 else obj.answer
    answer_preview.short_description = 'Answer Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question', 'user')


@admin.register(AnswerHelpful)
class AnswerHelpfulAdmin(admin.ModelAdmin):
    list_display = ['id', 'answer', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'answer__answer']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['answer', 'user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('answer', 'user')
