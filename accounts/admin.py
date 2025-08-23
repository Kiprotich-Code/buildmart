from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Seller


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'is_email_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('email', 'role', 'is_email_verified')}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'user_role', 'phone', 'created_at')
    list_filter = ('user__role', 'created_at')
    search_fields = ('full_name', 'user__email', 'phone')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def user_role(self, obj):
        return obj.user.role
    user_role.short_description = 'Role'


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'verification_status', 'state', 'city', 'subscription_active', 'created_at')
    list_filter = ('verification_status', 'subscription_active', 'state', 'created_at')
    search_fields = ('shop_name', 'user__email', 'business_license', 'city')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'shop_name', 'shop_description')
        }),
        ('Business Details', {
            'fields': ('business_license', 'tax_id', 'union_membership_number')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state')
        }),
        ('Verification', {
            'fields': ('verification_status',)
        }),
        ('Subscription', {
            'fields': ('trial_end_date', 'subscription_active', 'subscription_end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
