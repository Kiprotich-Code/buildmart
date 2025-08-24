from rest_framework import serializers
from .models import Category, Product, ProductReview, Boost


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'parent', 'is_active', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing categories"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'images', 'category', 'category_name', 'seller', 'seller_name', 'is_active', 'is_boosted', 'boost_expires_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'seller', 'created_at', 'updated_at']


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_name', 'rating', 'comment', 'is_verified_purchase', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class BoostSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Boost
        fields = ['id', 'product', 'product_name', 'seller', 'reach_type', 'duration_days', 'cost', 'starts_at', 'expires_at', 'is_paid', 'created_at']
        read_only_fields = ['id', 'seller', 'starts_at', 'created_at']
