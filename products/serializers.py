from rest_framework import serializers
from .models import Category, Product, ProductReview, Boost, ProductImage
from .utils import validate_image


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


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images"""
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'thumbnail', 'alt_text', 'order', 'width', 'height', 'file_size', 'created_at']
        read_only_fields = ['id', 'thumbnail', 'width', 'height', 'file_size', 'created_at']

    def validate_image(self, value):
        """Validate uploaded image"""
        validate_image(value)
        return value


class ProductImageUploadSerializer(serializers.Serializer):
    """Serializer for bulk image upload"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        max_length=10,  # Maximum 10 images per product
        help_text="List of image files to upload"
    )
    alt_texts = serializers.ListField(
        child=serializers.CharField(max_length=255, required=False, allow_blank=True),
        required=False,
        help_text="Optional list of alt texts for images (same order as images)"
    )

    def validate_images(self, value):
        """Validate all uploaded images"""
        for image in value:
            validate_image(image)
        return value

    def validate(self, data):
        """Validate that alt_texts length matches images length if provided"""
        images = data.get('images', [])
        alt_texts = data.get('alt_texts', [])
        
        if alt_texts and len(alt_texts) != len(images):
            raise serializers.ValidationError(
                "Number of alt texts must match number of images"
            )
        
        return data


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing products"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    images = serializers.ReadOnlyField()  # Uses the @property method
    image_urls = serializers.ReadOnlyField()
    thumbnail_urls = serializers.ReadOnlyField()
    primary_image_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'quantity', 'images', 'image_urls', 'thumbnail_urls', 'primary_image_url', 
                  'category', 'category_name', 'seller', 'seller_name', 'is_active', 'is_boosted', 
                  'review_count', 'average_rating', 'created_at']
    
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
    product_images = ProductImageSerializer(many=True, read_only=True)
    images = serializers.ReadOnlyField()  # Uses the @property method for backward compatibility
    image_urls = serializers.ReadOnlyField()
    thumbnail_urls = serializers.ReadOnlyField()
    primary_image_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'images', 'image_urls', 'thumbnail_urls',
                  'primary_image_url', 'product_images', 'category', 'category_name', 'seller', 'seller_name', 
                  'seller_email', 'is_active', 'is_boosted', 'boost_expires_at', 'review_count', 'average_rating', 
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


class ProductCreateWithImagesSerializer(serializers.ModelSerializer):
    """Serializer for creating a product with images in one API call"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        max_length=10,
        help_text="List of image files to upload with the product"
    )
    alt_texts = serializers.ListField(
        child=serializers.CharField(max_length=255, required=False, allow_blank=True),
        required=False,
        help_text="Optional list of alt texts for images (same order as images)"
    )
    
    # Read-only fields to return the created product with image data
    product_images = ProductImageSerializer(many=True, read_only=True)
    image_urls = serializers.ReadOnlyField()
    thumbnail_urls = serializers.ReadOnlyField()
    primary_image_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'quantity', 'category', 'images', 'alt_texts',
                  'product_images', 'image_urls', 'thumbnail_urls', 'primary_image_url', 'is_active', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'seller', 'created_at', 'updated_at']
    
    def validate_images(self, value):
        """Validate all uploaded images"""
        if value:
            for image in value:
                validate_image(image)
        return value
    
    def validate(self, data):
        """Validate that alt_texts length matches images length if provided"""
        images = data.get('images', [])
        alt_texts = data.get('alt_texts', [])
        
        if alt_texts and len(alt_texts) != len(images):
            raise serializers.ValidationError(
                "Number of alt texts must match number of images"
            )
        
        return data
    
    def create(self, validated_data):
        """Create product and process images in one transaction"""
        # Extract image-related data
        images = validated_data.pop('images', [])
        alt_texts = validated_data.pop('alt_texts', [])
        
        # Set seller from request context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['seller'] = request.user
        
        # Create the product
        product = Product.objects.create(**validated_data)
        
        # Process and create images if provided
        if images:
            from .utils import process_uploaded_images
            created_images = process_uploaded_images(images, product)
            
            # Set alt texts if provided
            if alt_texts:
                for i, alt_text in enumerate(alt_texts):
                    if i < len(created_images) and alt_text:
                        created_images[i].alt_text = alt_text
                        created_images[i].save()
        
        return product
