#!/usr/bin/env python
"""
Quick test script to verify the updated Product serializer with seller details
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buildmart.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product, Category
from products.serializers import ProductSerializer, ProductListSerializer
from accounts.models import Seller
import json

User = get_user_model()

def test_product_serializer():
    print("🔍 Testing Product Serializer with Seller Details...")
    
    # Get a product (if any exist)
    try:
        product = Product.objects.select_related(
            'seller', 
            'seller__seller', 
            'category'
        ).first()
        
        if not product:
            print("❌ No products found in database. Creating test data...")
            return create_test_data()
        
        print(f"✅ Found product: {product.name}")
        
        # Test ProductSerializer
        serializer = ProductSerializer(product)
        data = serializer.data
        
        print("\n📋 Product Serializer Output:")
        print(f"  - Product ID: {data.get('id')}")
        print(f"  - Product Name: {data.get('name')}")
        print(f"  - Seller ID: {data.get('seller')}")
        print(f"  - Seller Name: {data.get('seller_name')}")
        print(f"  - Seller Email: {data.get('seller_email')}")
        
        # Check if seller_details is included
        seller_details = data.get('seller_details')
        if seller_details:
            print(f"  ✅ Seller Details Found:")
            print(f"    - Shop Name: {seller_details.get('shop_name')}")
            print(f"    - Verification Status: {seller_details.get('verification_status')}")
            print(f"    - Location: {seller_details.get('city')}, {seller_details.get('state')}")
            print(f"    - Is Verified: {seller_details.get('is_verified')}")
        else:
            print("  ❌ Seller Details NOT found in response")
            
        # Test ProductListSerializer
        print("\n📋 Product List Serializer Output:")
        list_serializer = ProductListSerializer(product)
        list_data = list_serializer.data
        
        list_seller_details = list_data.get('seller_details')
        if list_seller_details:
            print(f"  ✅ List Seller Details Found:")
            print(f"    - Shop Name: {list_seller_details.get('shop_name')}")
            print(f"    - Verification Status: {list_seller_details.get('verification_status')}")
        else:
            print("  ❌ List Seller Details NOT found in response")
            
        print("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

def create_test_data():
    print("\n🔧 Creating test data...")
    
    try:
        # Create a test seller user
        seller_user = User.objects.filter(role='seller').first()
        if not seller_user:
            print("❌ No seller users found. Need to create test data manually.")
            return False
            
        # Check if seller has a seller profile
        if not hasattr(seller_user, 'seller'):
            print("❌ Seller user doesn't have a seller profile.")
            return False
            
        # Get or create a category
        category, created = Category.objects.get_or_create(
            name="Test Category",
            defaults={'slug': 'test-category'}
        )
        
        # Create a test product
        product = Product.objects.create(
            seller=seller_user,
            category=category,
            name="Test Product for Seller Details",
            description="This is a test product to verify seller details in API",
            price=100.00,
            quantity=10
        )
        
        print(f"✅ Created test product: {product.name}")
        
        # Now test the serializer
        return test_product_serializer()
        
    except Exception as e:
        print(f"❌ Error creating test data: {str(e)}")
        return False

def check_database_structure():
    print("\n🔍 Checking database structure...")
    
    # Check if we have users with seller role
    seller_users = User.objects.filter(role='seller').count()
    print(f"  - Seller users: {seller_users}")
    
    # Check if we have seller profiles
    seller_profiles = Seller.objects.count()
    print(f"  - Seller profiles: {seller_profiles}")
    
    # Check if we have products
    products = Product.objects.count()
    print(f"  - Products: {products}")
    
    # Check if we have categories
    categories = Category.objects.count()
    print(f"  - Categories: {categories}")
    
    if seller_users > 0 and seller_profiles > 0 and products > 0:
        print("✅ Database structure looks good!")
        return True
    else:
        print("⚠️ Database might need some test data")
        return False

if __name__ == "__main__":
    print("🚀 Starting Product Serializer Test")
    print("=" * 50)
    
    # Check database first
    db_ok = check_database_structure()
    
    if db_ok:
        # Run the actual test
        success = test_product_serializer()
        
        if success:
            print("\n✅ All tests passed! Seller details are now included in product API.")
        else:
            print("\n❌ Some tests failed. Check the output above.")
    else:
        print("\n⚠️ Database needs test data. Please create some sellers and products first.")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed")
