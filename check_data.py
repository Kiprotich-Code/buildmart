import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/fleek/drf/buildmart')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buildmart.settings')
django.setup()

from products.models import Product, Category
from accounts.models import CustomUser, Seller

print("=== DATABASE STATUS ===")
print(f"Users count: {CustomUser.objects.count()}")
print(f"Sellers count: {Seller.objects.count()}")
print(f"Categories count: {Category.objects.count()}")
print(f"Products count: {Product.objects.count()}")

print("\n=== PRODUCTS ===")
for product in Product.objects.all():
    print(f"- {product.name}")
    print(f"  Price: ${product.price}")
    print(f"  Seller: {product.seller.seller.shop_name}")
    print(f"  Category: {product.category.name}")
    print(f"  Quantity: {product.quantity}")
    print(f"  Active: {product.is_active}")
    print()
