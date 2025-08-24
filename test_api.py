import os
import sys
import django
import json

# Add the project directory to the Python path
sys.path.append('/home/fleek/drf/buildmart')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buildmart.settings')
django.setup()

from django.test import Client
from django.urls import reverse

client = Client()

print("=== TESTING API ENDPOINTS ===")

# Test products list
print("\n1. Testing Products List:")
response = client.get('/api/products/products/')
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Products returned: {len(data)}")
    for product in data:
        print(f"  - {product['name']} (${product['price']})")
else:
    print(f"Error: {response.content}")

# Test categories list
print("\n2. Testing Categories List:")
response = client.get('/api/products/categories/')
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Categories returned: {len(data)}")
    for category in data[:5]:  # Show first 5
        print(f"  - {category['name']} (Products: {category['product_count']})")
else:
    print(f"Error: {response.content}")

# Test featured products
print("\n3. Testing Featured Products:")
response = client.get('/api/products/products/featured/')
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Featured products: {len(data)}")
else:
    print(f"Error: {response.content}")

# Test product filtering by category
print("\n4. Testing Product Filtering by Category:")
response = client.get('/api/products/products/?category=f1c28ad9-613e-4fcc-8790-f4a07a9a3a14')
print(f"Status Code: {response.status_code}")

print("\n=== API TESTS COMPLETED ===")
