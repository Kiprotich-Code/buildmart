from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Report, Flag


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
