from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
from django.utils import timezone
import uuid

User = get_user_model()

class BoostPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    features = models.JSONField()

    def __str__(self):
        return self.name

class Boost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boosts_user')
    listing = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boosts_listing')
    plan = models.ForeignKey(BoostPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')],
        default='pending'
    )
    tx_ref = models.CharField(max_length=100, unique=True, default=uuid.uuid4)

    def __str__(self):
        return f"{self.plan.name} for {self.listing.name} by {self.user.username}"

    def save(self, *args, **kwargs):
        if self.payment_status == 'paid' and not self.start_date:
            self.start_date = timezone.now()
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
            self.is_active = True
        super().save(*args, **kwargs)   