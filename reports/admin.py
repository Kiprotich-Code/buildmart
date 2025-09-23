from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Report, Flag, Dispute, DisputeMessage


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'type', 'reported_item_title_short', 'reporter_name_short',
        'reported_user_name_short', 'reason', 'status', 'priority',
        'created_at', 'admin_actions'
    ]
    list_filter = [
        'status', 'priority', 'type', 'reason', 'created_at'
    ]
    search_fields = [
        'id', 'description', 'reporter__email', 'reporter__username',
        'reported_user__email', 'reported_user__username'
    ]
    readonly_fields = [
        'id', 'type', 'reporter', 'reported_user', 'created_at',
        'updated_at', 'reported_item_link'
    ]
    fieldsets = (
        ('Report Information', {
            'fields': ('id', 'type', 'reporter', 'reported_user', 'reported_item_link')
        }),
        ('Report Details', {
            'fields': ('reason', 'description', 'evidence_urls')
        }),
        ('Admin Management', {
            'fields': ('status', 'priority', 'assigned_admin', 'admin_notes', 'resolution')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        })
    )
    actions = ['mark_as_investigating', 'mark_as_resolved', 'mark_as_dismissed']
    
    def reported_item_title_short(self, obj):
        title = obj.reported_item_title
        return title[:50] + '...' if len(title) > 50 else title
    reported_item_title_short.short_description = 'Reported Item'
    
    def reporter_name_short(self, obj):
        return obj.reporter_name[:30] + '...' if len(obj.reporter_name) > 30 else obj.reporter_name
    reporter_name_short.short_description = 'Reporter'
    
    def reported_user_name_short(self, obj):
        name = obj.reported_user_name or 'N/A'
        return name[:30] + '...' if len(name) > 30 else name
    reported_user_name_short.short_description = 'Reported User'
    
    def reported_item_link(self, obj):
        if obj.reported_item:
            # Create a link to view the reported item in admin
            app_label = obj.content_type.app_label
            model = obj.content_type.model
            url = reverse(f'admin:{app_label}_{model}_change', args=[obj.object_id])
            return format_html('<a href="{}" target="_blank">View {}</a>', url, obj.reported_item_title)
        return 'N/A'
    reported_item_link.short_description = 'Reported Item Link'
    
    def admin_actions(self, obj):
        actions = []
        if obj.status == 'pending':
            actions.append('<span style="color: orange;">⏳ Pending</span>')
        elif obj.status == 'investigating':
            actions.append('<span style="color: blue;">🔍 Investigating</span>')
        elif obj.status == 'resolved':
            actions.append('<span style="color: green;">✅ Resolved</span>')
        elif obj.status == 'dismissed':
            actions.append('<span style="color: red;">❌ Dismissed</span>')
        
        if obj.priority == 'critical':
            actions.append('<span style="color: red; font-weight: bold;">🚨 CRITICAL</span>')
        elif obj.priority == 'high':
            actions.append('<span style="color: orange; font-weight: bold;">⚠️ HIGH</span>')
        
        return format_html(' '.join(actions))
    admin_actions.short_description = 'Status & Priority'
    
    def mark_as_investigating(self, request, queryset):
        queryset.update(status='investigating')
        self.message_user(request, f'{queryset.count()} reports marked as investigating.')
    mark_as_investigating.short_description = 'Mark as investigating'
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} reports marked as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def mark_as_dismissed(self, request, queryset):
        queryset.update(status='dismissed')
        self.message_user(request, f'{queryset.count()} reports marked as dismissed.')
    mark_as_dismissed.short_description = 'Mark as dismissed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'reporter', 'reported_user', 'assigned_admin', 'content_type'
        )


@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'item_type', 'item_title_short', 'flag_type',
        'severity', 'status', 'flagged_by', 'manual_review_required',
        'flagged_at', 'flag_indicators'
    ]
    list_filter = [
        'status', 'severity', 'item_type', 'flag_type',
        'manual_review_required', 'flagged_at'
    ]
    search_fields = [
        'id', 'reason', 'flagged_by', 'admin_notes'
    ]
    readonly_fields = [
        'id', 'flagged_at', 'flagged_item_link'
    ]
    fieldsets = (
        ('Flag Information', {
            'fields': ('id', 'item_type', 'flagged_item_link', 'flag_type')
        }),
        ('Flag Details', {
            'fields': ('reason', 'severity', 'flagged_by', 'flagged_by_user')
        }),
        ('Review & Actions', {
            'fields': ('status', 'manual_review_required', 'auto_actions_taken',
                      'admin_notes', 'reviewed_by')
        }),
        ('Timestamps', {
            'fields': ('flagged_at', 'reviewed_at'),
            'classes': ('collapse',)
        })
    )
    actions = ['mark_as_resolved', 'mark_as_ignored', 'require_manual_review']
    
    def item_title_short(self, obj):
        title = obj.item_title
        return title[:50] + '...' if len(title) > 50 else title
    item_title_short.short_description = 'Item'
    
    def flagged_item_link(self, obj):
        if obj.flagged_item:
            # Create a link to view the flagged item in admin
            app_label = obj.content_type.app_label
            model = obj.content_type.model
            url = reverse(f'admin:{app_label}_{model}_change', args=[obj.object_id])
            return format_html('<a href="{}" target="_blank">View {}</a>', url, obj.item_title)
        return 'N/A'
    flagged_item_link.short_description = 'Flagged Item Link'
    
    def flag_indicators(self, obj):
        indicators = []
        
        # Status indicator
        if obj.status == 'active':
            indicators.append('<span style="color: red;">🔴 Active</span>')
        elif obj.status == 'resolved':
            indicators.append('<span style="color: green;">✅ Resolved</span>')
        elif obj.status == 'ignored':
            indicators.append('<span style="color: gray;">⚫ Ignored</span>')
        elif obj.status == 'escalated':
            indicators.append('<span style="color: purple;">🔺 Escalated</span>')
        
        # Severity indicator
        if obj.severity == 'critical':
            indicators.append('<span style="color: red; font-weight: bold;">🚨 CRITICAL</span>')
        elif obj.severity == 'high':
            indicators.append('<span style="color: orange; font-weight: bold;">⚠️ HIGH</span>')
        
        # Review indicator
        if obj.manual_review_required:
            indicators.append('<span style="color: blue;">👁️ Review Required</span>')
        
        # Auto actions indicator
        if obj.auto_actions_taken:
            indicators.append('<span style="color: purple;">🤖 Auto Actions</span>')
        
        return format_html(' '.join(indicators))
    flag_indicators.short_description = 'Indicators'
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', reviewed_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{queryset.count()} flags marked as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def mark_as_ignored(self, request, queryset):
        queryset.update(status='ignored', reviewed_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{queryset.count()} flags marked as ignored.')
    mark_as_ignored.short_description = 'Mark as ignored'
    
    def require_manual_review(self, request, queryset):
        queryset.update(manual_review_required=True)
        self.message_user(request, f'{queryset.count()} flags marked for manual review.')
    require_manual_review.short_description = 'Require manual review'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'flagged_by_user', 'reviewed_by', 'content_type'
        )


# Customize admin site headers
admin.site.site_header = "BuildMart Admin"
admin.site.site_title = "BuildMart Admin Portal"
admin.site.index_title = "Welcome to BuildMart Administration"


class DisputeMessageInline(admin.TabularInline):
    model = DisputeMessage
    fields = ['sender', 'message_type', 'content', 'created_at']
    readonly_fields = ['created_at']
    extra = 0
    can_delete = False
    ordering = ['created_at']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title_short', 'buyer_name', 'seller_name', 'product_name',
        'status', 'admin_joined', 'is_resolved', 'created_at', 'dispute_actions'
    ]
    list_filter = [
        'status', 'is_resolved', 'admin_joined', 'resolution_type', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'buyer__email', 'seller__email',
        'product__name', 'admin_decision'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'resolved_at', 'last_message_at',
        'escalated_from_chat_link', 'participants_list'
    ]
    fieldsets = (
        ('Dispute Information', {
            'fields': ('id', 'title', 'description', 'status')
        }),
        ('Participants', {
            'fields': ('buyer', 'seller', 'product', 'participants_list')
        }),
        ('Admin Management', {
            'fields': ('admin_joined', 'admin_user', 'admin_decision')
        }),
        ('Resolution', {
            'fields': (
                'is_resolved', 'resolution_type', 'resolution_description',
                'buyer_marked_resolved', 'seller_marked_resolved'
            )
        }),
        ('Evidence & Links', {
            'fields': ('evidence_urls', 'escalated_from_chat_link'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at', 'last_message_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [DisputeMessageInline]
    actions = ['mark_as_resolved', 'join_as_admin', 'mark_in_progress']
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def buyer_name(self, obj):
        if hasattr(obj.buyer, 'profile') and obj.buyer.profile.full_name:
            return obj.buyer.profile.full_name
        return obj.buyer.email
    buyer_name.short_description = 'Buyer'
    
    def seller_name(self, obj):
        if hasattr(obj.seller, 'profile') and obj.seller.profile.full_name:
            return obj.seller.profile.full_name
        return obj.seller.email
    seller_name.short_description = 'Seller'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else 'No Product'
    product_name.short_description = 'Product'
    
    def participants_list(self, obj):
        participants = [
            f"👤 Buyer: {self.buyer_name(obj)}",
            f"🏪 Seller: {self.seller_name(obj)}"
        ]
        if obj.admin_joined and obj.admin_user:
            admin_name = obj.admin_user.profile.full_name if hasattr(obj.admin_user, 'profile') and obj.admin_user.profile.full_name else obj.admin_user.email
            participants.append(f"👨‍💼 Admin: {admin_name}")
        return format_html('<br>'.join(participants))
    participants_list.short_description = 'Participants'
    
    def escalated_from_chat_link(self, obj):
        if obj.escalated_from_chat:
            url = reverse('admin:chats_chat_change', args=[obj.escalated_from_chat.id])
            return format_html('<a href="{}">View Original Chat</a>', url)
        return 'Direct Dispute'
    escalated_from_chat_link.short_description = 'Original Chat'
    
    def dispute_actions(self, obj):
        indicators = []
        
        # Status indicator
        status_colors = {
            'open': 'orange',
            'in_progress': 'blue',
            'resolved': 'green',
            'closed': 'gray'
        }
        indicators.append(f'<span style="color: {status_colors.get(obj.status, "black")};">●</span>')
        
        # Admin involvement
        if obj.admin_joined:
            indicators.append('<span style="color: purple;">👨‍💼</span>')
        
        # Resolution status
        if obj.is_resolved:
            indicators.append('<span style="color: green;">✅</span>')
        elif obj.buyer_marked_resolved and obj.seller_marked_resolved:
            indicators.append('<span style="color: orange;">⏳</span>')
        
        # Message count
        message_count = obj.messages.count()
        indicators.append(f'<span title="Messages">💬 {message_count}</span>')
        
        return format_html(' '.join(indicators))
    dispute_actions.short_description = 'Status'
    
    def mark_as_resolved(self, request, queryset):
        for dispute in queryset:
            if not dispute.is_resolved:
                dispute.mark_resolved_by_admin(
                    request.user, 
                    "Resolved by admin via bulk action"
                )
        self.message_user(request, f'{queryset.count()} disputes marked as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved by admin'
    
    def join_as_admin(self, request, queryset):
        joined_count = 0
        for dispute in queryset:
            if not dispute.admin_joined:
                dispute.join_admin(request.user)
                joined_count += 1
        self.message_user(request, f'Joined {joined_count} disputes as admin.')
    join_as_admin.short_description = 'Join as admin'
    
    def mark_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
        self.message_user(request, f'{queryset.count()} disputes marked as in progress.')
    mark_in_progress.short_description = 'Mark as in progress'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'buyer', 'seller', 'product', 'admin_user', 'escalated_from_chat'
        ).prefetch_related('messages')


@admin.register(DisputeMessage)
class DisputeMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'dispute_title_short', 'sender_name', 'message_type',
        'content_short', 'created_at', 'read_status'
    ]
    list_filter = [
        'message_type', 'created_at', 'is_edited'
    ]
    search_fields = [
        'content', 'sender__email', 'dispute__title'
    ]
    readonly_fields = [
        'id', 'dispute', 'sender', 'created_at', 'edited_at'
    ]
    fieldsets = (
        ('Message Information', {
            'fields': ('id', 'dispute', 'sender', 'message_type')
        }),
        ('Content', {
            'fields': ('content', 'attachments')
        }),
        ('Read Status', {
            'fields': (
                'is_read_by_buyer', 'is_read_by_seller', 'is_read_by_admin'
            )
        }),
        ('Meta', {
            'fields': ('is_edited', 'created_at', 'edited_at'),
            'classes': ('collapse',)
        })
    )
    
    def dispute_title_short(self, obj):
        title = obj.dispute.title
        return title[:30] + '...' if len(title) > 30 else title
    dispute_title_short.short_description = 'Dispute'
    
    def sender_name(self, obj):
        if hasattr(obj.sender, 'profile') and obj.sender.profile.full_name:
            return obj.sender.profile.full_name
        return obj.sender.email
    sender_name.short_description = 'Sender'
    
    def content_short(self, obj):
        content = obj.content
        return content[:100] + '...' if len(content) > 100 else content
    content_short.short_description = 'Content'
    
    def read_status(self, obj):
        indicators = []
        if obj.is_read_by_buyer:
            indicators.append('👤')
        if obj.is_read_by_seller:
            indicators.append('🏪')
        if obj.is_read_by_admin:
            indicators.append('👨‍💼')
        
        if not indicators:
            return '📬 Unread'
        return f'📖 Read by: {" ".join(indicators)}'
    read_status.short_description = 'Read Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'dispute', 'sender'
        )
