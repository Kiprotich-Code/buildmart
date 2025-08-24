from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product
from accounts.models import Seller
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed product data into the database'

    def handle(self, *args, **options):
        # Mock product data
        mock_products = [
            {
                "name": "Premium Cement - 50kg",
                "price": 4500,
                "quantity": 100,
                "images": ["/src/assets/cement-slide-1.jpg"],
                "category_slug": "cement",
                "description": "High-quality cement perfect for construction projects. 50kg bag.",
                "seller": {
                    "email": "bigmaterials@example.com",
                    "first_name": "John",
                    "last_name": "Materials",
                    "shop_name": "Big Materials Shop",
                    "city": "Lagos",
                    "state": "Lagos",
                    "is_verified": True
                }
            },
            {
                "name": "Steel Rods - 12mm",
                "price": 850,
                "quantity": 200,
                "images": ["/src/assets/steel-rods-slide-1.jpg"],
                "category_slug": "steel",
                "description": "Durable 12mm steel rods for reinforced concrete construction.",
                "seller": {
                    "email": "qualitysteel@example.com",
                    "first_name": "Jane",
                    "last_name": "Steel",
                    "shop_name": "Quality Steel Ltd",
                    "city": "Abuja",
                    "state": "FCT",
                    "is_verified": True
                }
            },
            {
                "name": "Aluminum Sheets",
                "price": 15000,
                "quantity": 50,
                "images": ["/src/assets/aluminum-sheets-slide-1.jpg"],
                "category_slug": "others",  # Using 'others' since there's no aluminum category
                "description": "Premium aluminum sheets for roofing and construction applications.",
                "seller": {
                    "email": "metromaterials@example.com",
                    "first_name": "Mike",
                    "last_name": "Metro",
                    "shop_name": "Metro Materials",
                    "city": "Port Harcourt",
                    "state": "Rivers",
                    "is_verified": False
                }
            }
        ]

        created_count = 0
        updated_count = 0

        for product_data in mock_products:
            try:
                # Get or create seller user
                seller_data = product_data['seller']
                user, user_created = User.objects.get_or_create(
                    email=seller_data['email'],
                    defaults={
                        'username': seller_data['email'],
                        'first_name': seller_data['first_name'],
                        'last_name': seller_data['last_name'],
                        'role': 'seller'
                    }
                )
                
                if user_created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created user: {user.email}')
                    )

                # Get or create seller profile
                seller, seller_created = Seller.objects.get_or_create(
                    user=user,
                    defaults={
                        'shop_name': seller_data['shop_name'],
                        'city': seller_data['city'],
                        'state': seller_data['state'],
                        'address': f"{seller_data['city']}, {seller_data['state']}",
                        'verification_status': 'verified' if seller_data['is_verified'] else 'pending',
                        'trial_end_date': timezone.now() + timedelta(days=30),
                        'shop_description': f"Quality building materials supplier in {seller_data['city']}"
                    }
                )
                
                if seller_created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created seller: {seller.shop_name}')
                    )

                # Get category
                try:
                    category = Category.objects.get(slug=product_data['category_slug'])
                except Category.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Category with slug "{product_data["category_slug"]}" not found. Skipping product: {product_data["name"]}')
                    )
                    continue

                # Create or update product
                product, product_created = Product.objects.get_or_create(
                    name=product_data['name'],
                    seller=user,
                    defaults={
                        'description': product_data['description'],
                        'price': product_data['price'],
                        'quantity': product_data['quantity'],
                        'images': product_data['images'],
                        'category': category,
                        'is_active': True
                    }
                )
                
                if product_created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created product: {product.name}')
                    )
                else:
                    # Update existing product
                    product.description = product_data['description']
                    product.price = product_data['price']
                    product.quantity = product_data['quantity']
                    product.images = product_data['images']
                    product.category = category
                    product.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated product: {product.name}')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing product {product_data["name"]}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Seeding completed! Created: {created_count}, Updated: {updated_count}')
        )
