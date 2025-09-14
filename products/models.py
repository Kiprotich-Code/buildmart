from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.core.validators import MinValueValidator
from decimal import Decimal
from .utils import generate_image_filename, delete_image_file

User = get_user_model()

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=10, blank=True, null=True, help_text="Emoji icon for the category")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    # Legacy field - kept for backward compatibility but deprecated
    legacy_images = models.JSONField(default=list, blank=True, help_text="Deprecated - use ProductImage model")
    is_active = models.BooleanField(default=True)
    is_boosted = models.BooleanField(default=False)
    boost_expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name

    @property
    def images(self):
        """
        Backward compatibility property - returns list of image URLs
        """
        # Priority: ProductImage objects first, then legacy_images as fallback
        product_images = self.product_images.filter(is_active=True).order_by('order')
        if product_images.exists():
            return [img.image.url for img in product_images]
        return self.legacy_images or []

    @property
    def image_urls(self):
        """Get all image URLs for this product"""
        return [img.image.url for img in self.product_images.filter(is_active=True).order_by('order')]

    @property
    def thumbnail_urls(self):
        """Get all thumbnail URLs for this product"""
        return [img.thumbnail.url if img.thumbnail else img.image.url 
                for img in self.product_images.filter(is_active=True).order_by('order')]

    @property
    def primary_image(self):
        """Get the primary (first) image for this product"""
        return self.product_images.filter(is_active=True).order_by('order').first()

    @property
    def primary_image_url(self):
        """Get the first (primary) image URL"""
        first_image = self.primary_image
        if first_image:
            return first_image.image.url
        # Fallback to legacy images
        if self.legacy_images:
            return self.legacy_images[0]
        return None


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to=generate_image_filename)
    thumbnail = models.ImageField(upload_to=generate_image_filename, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, help_text="Alternative text for accessibility")
    order = models.PositiveIntegerField(default=0, help_text="Display order (0 = primary image)")
    is_active = models.BooleanField(default=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_images'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_active', 'order']),
        ]

    def __str__(self):
        return f"Image for {self.product.name} (Order: {self.order})"

    def delete(self, *args, **kwargs):
        """Override delete to clean up image files"""
        # Delete image files from storage
        if self.image:
            delete_image_file(self.image.name)
        if self.thumbnail:
            delete_image_file(self.thumbnail.name)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Override save to process images"""
        from .utils import process_image, create_thumbnail, get_image_dimensions, PILLOW_AVAILABLE
        
        if self.image and not self.pk:  # New image upload
            # Process the main image
            processed_image = process_image(self.image)
            self.image.save(self.image.name, processed_image, save=False)
            
            # Get image dimensions if Pillow is available
            if PILLOW_AVAILABLE:
                self.width, self.height = get_image_dimensions(self.image)
            
            self.file_size = self.image.size
            
            # Create thumbnail if Pillow is available
            if PILLOW_AVAILABLE:
                thumbnail = create_thumbnail(self.image)
                if thumbnail:
                    thumbnail_name = f"thumb_{self.image.name.split('/')[-1]}"
                    self.thumbnail.save(thumbnail_name, thumbnail, save=False)
        
        super().save(*args, **kwargs)


class ProductReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1)])  # 1-5 rating
    comment = models.TextField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_reviews'
        constraints = [
            models.UniqueConstraint(fields=['product', 'user'], name='unique_user_product_review'),
            models.CheckConstraint(check=models.Q(rating__gte=1, rating__lte=5), name='valid_rating_range')
        ]

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email}"


class Boost(models.Model):
    REACH_CHOICES = [
        ('local', 'Local'),
        ('state', 'State'),
        ('national', 'National')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boosts')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boosts')
    reach_type = models.CharField(max_length=20, choices=REACH_CHOICES)
    duration_days = models.IntegerField(validators=[MinValueValidator(1)])
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    starts_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'boosts'

    def __str__(self):
        return f"Boost for {self.product.name} ({self.reach_type})"