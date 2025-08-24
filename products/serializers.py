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


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing products"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'quantity', 'images', 'category', 'category_name', 
                  'seller', 'seller_name', 'is_active', 'is_boosted', 'review_count', 
                  'average_rating', 'created_at']
    
    def get_review_count(self, obj):
        return obj.reviews.count()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return None


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    seller_email = serializers.CharField(source='seller.email', read_only=True)
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    can_chat = serializers.SerializerMethodField()
    existing_chat_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'images', 'category', 
                  'category_name', 'seller', 'seller_name', 'seller_email', 'is_active', 
                  'is_boosted', 'boost_expires_at', 'review_count', 'average_rating', 
                  'recent_reviews', 'can_chat', 'existing_chat_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'seller', 'created_at', 'updated_at']
    
    def get_review_count(self, obj):
        return obj.reviews.count()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return None
    
    def get_recent_reviews(self, obj):
        recent_reviews = obj.reviews.order_by('-created_at')[:3]
        return ProductReviewSerializer(recent_reviews, many=True).data
    
    def get_can_chat(self, obj):
        """Check if current user can chat about this product"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Users can't chat with themselves
        if request.user == obj.seller:
            return False
        
        # Product must be active
        return obj.is_active
    
    def get_existing_chat_id(self, obj):
        """Get existing chat ID if user already has a chat about this product"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Import here to avoid circular imports
        from chats.models import Chat
        
        try:
            chat = Chat.objects.get(
                buyer=request.user,
                seller=obj.seller,
                product=obj,
                is_active=True
            )
            return str(chat.id)
        except Chat.DoesNotExist:
            return None


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
