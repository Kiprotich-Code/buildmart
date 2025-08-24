from django.contrib import admin
from .models import Category, Product, ProductReview, Boost

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'seller', 'price', 'quantity', 'is_active', 'is_boosted']
    list_filter = ['category', 'is_active', 'is_boosted', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_verified_purchase', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Boost)
class BoostAdmin(admin.ModelAdmin):
    list_display = ['product', 'seller', 'reach_type', 'duration_days', 'cost', 'is_paid', 'expires_at']
    list_filter = ['reach_type', 'is_paid', 'created_at']
    search_fields = ['product__name', 'seller__email']
    readonly_fields = ['id', 'created_at']
