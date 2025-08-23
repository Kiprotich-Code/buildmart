from django.db import models
from django.contrib.auth.models import User
import uuid
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import ArrayField

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.TextField()
    phone = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    user_type = models.CharField(
        max_length=20,
        choices=[('buyer', 'Buyer'), ('seller', 'Seller'), ('admin', 'Admin')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_profile')
        ]

    def __str__(self):
        return f"{self.full_name} ({self.user_type})"

class Seller(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller')
    shop_name = models.TextField()
    state = models.TextField()
    city = models.TextField()
    union_membership_number = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    trial_end_date = models.DateTimeField()
    subscription_active = models.BooleanField(default=True)
    subscription_end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sellers'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_seller')
        ]

    def __str__(self):
        return self.shop_name

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    slug = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    images = ArrayField(models.TextField(), default=list, blank=True)
    is_active = models.BooleanField(default=True)
    is_boosted = models.BooleanField(default=False)
    boost_expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name

class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_chats')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    last_message_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chats'
        constraints = [
            models.UniqueConstraint(fields=['buyer', 'seller', 'product'], name='unique_chat')
        ]

    def __str__(self):
        return f"Chat between {self.buyer.username} and {self.seller.username}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'

    def __str__(self):
        return f"Message in {self.chat.id} by {self.sender.username}"

class Boost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boosts')
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='boosts')
    reach_type = models.CharField(
        max_length=20,
        choices=[('local', 'Local'), ('state', 'State'), ('national', 'National')]
    )
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