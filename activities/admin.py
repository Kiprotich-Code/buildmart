from django.contrib import admin
from .models import RecentActivity

@admin.register(RecentActivity)
class RecentActivityAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'message', 'user', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('message', 'user__email', 'user__username')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('action_type', 'message', 'user')
        }),
        ('Related Information', {
            'fields': ('related_object_id', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )
