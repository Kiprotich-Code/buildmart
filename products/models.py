from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import ArrayField

User = get_user_model()

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
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
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    images = ArrayField(models.URLField(), default=list, blank=True)
    is_active = models.BooleanField(default=True)
    is_boosted = models.BooleanField(default=False)
    boost_expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name


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
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    starts_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'boosts'

    def __str__(self):
        return f"Boost for {self.product.name} ({self.reach_type})"