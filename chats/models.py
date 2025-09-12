from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_chats')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    last_message_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chats'
        constraints = [
            models.UniqueConstraint(fields=['buyer', 'seller', 'product'], name='unique_chat')
        ]

    def __str__(self):
        return f"Chat between {self.buyer.email} and {self.seller.email}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    file_url = models.URLField(blank=True, null=True)  # For image/file messages
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message in {self.chat.id} by {self.sender.email}"


class ProductQuestion(models.Model):
    """Model to store questions about products"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asked_questions')
    question = models.TextField()
    is_answered = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_questions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Question by {self.user.email} about {self.product.name}"

    @property
    def answer_count(self):
        return self.answers.count()

    @property
    def latest_answer(self):
        return self.answers.order_by('-created_at').first()


class ProductAnswer(models.Model):
    """Model to store answers to product questions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='provided_answers')
    answer = models.TextField()
    is_seller_answer = models.BooleanField(default=False)  # True if answered by product seller
    is_verified = models.BooleanField(default=False)  # For highlighting verified answers
    helpful_count = models.PositiveIntegerField(default=0)  # Users can mark answers as helpful
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_answers'
        ordering = ['-is_seller_answer', '-helpful_count', '-created_at']  # Seller answers first, then by helpfulness

    def __str__(self):
        return f"Answer by {self.user.email} to question {self.question.id}"

    def save(self, *args, **kwargs):
        # Check if this answer is from the product seller
        if self.question.product.seller == self.user:
            self.is_seller_answer = True
        
        super().save(*args, **kwargs)
        
        # Update question's is_answered status
        self.question.is_answered = True
        self.question.save(update_fields=['is_answered'])


class AnswerHelpful(models.Model):
    """Model to track which users found answers helpful"""
    answer = models.ForeignKey(ProductAnswer, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='helpful_answers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'answer_helpful'
        unique_together = ['answer', 'user']  # One vote per user per answer

    def __str__(self):
        return f"{self.user.email} found answer {self.answer.id} helpful"
