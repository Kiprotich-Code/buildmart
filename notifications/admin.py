from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Notification, NotificationRead


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'notification_type', 'priority', 'target_audience', 
        'total_recipients', 'read_count', 'read_rate_display', 
        'created_by', 'is_active', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'target_audience', 
        'created_by', 'is_active', 'created_at'
    ]
    search_fields = ['title', 'message']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'total_recipients', 
        'read_count', 'read_rate', 'click_count', 'click_rate'
    ]
    filter_horizontal = ['specific_users']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'notification_type', 'priority', 'message')
        }),
        ('Targeting', {
            'fields': ('target_audience', 'specific_users')
        }),
        ('Actions', {
            'fields': ('action_buttons',),
            'description': 'JSON format: [{"text": "Button Text", "url": "https://example.com"}]'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_by_user', 'is_active', 'scheduled_for')
        }),
        ('Statistics', {
            'fields': (
                'total_recipients', 'read_count', 'read_rate', 
                'click_count', 'click_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def read_rate_display(self, obj):
        """Display read rate with color coding"""
        rate = obj.read_rate
        if rate >= 80:
            color = 'green'
        elif rate >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    read_rate_display.short_description = 'Read Rate'
    read_rate_display.admin_order_field = 'read_rate'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('created_by_user')
    
    def save_model(self, request, obj, form, change):
        """Set created_by_user if not set"""
        if not obj.created_by_user:
            obj.created_by_user = request.user
        super().save_model(request, obj, form, change)


@admin.register(NotificationRead)
class NotificationReadAdmin(admin.ModelAdmin):
    list_display = [
        'notification_title', 'user_email', 'read_at', 
        'clicked', 'clicked_at'
    ]
    list_filter = ['clicked', 'read_at', 'notification__notification_type']
    search_fields = ['notification__title', 'user__email', 'user__username']
    readonly_fields = ['id', 'read_at', 'clicked_at']
    date_hierarchy = 'read_at'
    
    def notification_title(self, obj):
        """Display notification title with link"""
        url = reverse('admin:notifications_notification_change', args=[obj.notification.id])
        return format_html('<a href="{}">{}</a>', url, obj.notification.title)
    notification_title.short_description = 'Notification'
    notification_title.admin_order_field = 'notification__title'
    
    def user_email(self, obj):
        """Display user email with link"""
        url = reverse('admin:accounts_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('notification', 'user')


# Customize admin site
admin.site.site_header = "BuildMart Notifications Admin"
admin.site.site_title = "Notifications Admin"
admin.site.index_title = "Notification Management"
