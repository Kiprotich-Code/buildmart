from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Product, Category
from chats.models import Chat, Message
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users, products, and chat data for testing the chat feature'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing test data before creating new data',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Deleting existing test data...')
            # Delete test chats and messages
            Chat.objects.filter(
                buyer__email__in=['buyer@test.com', 'buyer2@test.com'],
                seller__email__in=['seller@test.com', 'seller2@test.com']
            ).delete()
            
            # Delete test users (this will cascade to products)
            User.objects.filter(
                email__in=['buyer@test.com', 'buyer2@test.com', 'seller@test.com', 'seller2@test.com']
            ).delete()

        self.stdout.write('Creating test users...')
        
        # Create test buyer users
        buyer1, created = User.objects.get_or_create(
            email='buyer@test.com',
            defaults={
                'username': 'buyer_user',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'user',
                'is_email_verified': True
            }
        )
        if created:
            buyer1.set_password('testpass123')
            buyer1.save()
            self.stdout.write(f'✓ Created buyer: {buyer1.email}')
        else:
            self.stdout.write(f'✓ Buyer already exists: {buyer1.email}')

        buyer2, created = User.objects.get_or_create(
            email='buyer2@test.com',
            defaults={
                'username': 'buyer2_user',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'user',
                'is_email_verified': True
            }
        )
        if created:
            buyer2.set_password('testpass123')
            buyer2.save()
            self.stdout.write(f'✓ Created buyer: {buyer2.email}')
        else:
            self.stdout.write(f'✓ Buyer already exists: {buyer2.email}')

        # Create test seller users
        seller1, created = User.objects.get_or_create(
            email='seller@test.com',
            defaults={
                'username': 'seller_user',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': 'seller',
                'is_email_verified': True
            }
        )
        if created:
            seller1.set_password('testpass123')
            seller1.save()
            self.stdout.write(f'✓ Created seller: {seller1.email}')
        else:
            self.stdout.write(f'✓ Seller already exists: {seller1.email}')

        seller2, created = User.objects.get_or_create(
            email='seller2@test.com',
            defaults={
                'username': 'seller2_user',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'role': 'seller',
                'is_email_verified': True
            }
        )
        if created:
            seller2.set_password('testpass123')
            seller2.save()
            self.stdout.write(f'✓ Created seller: {seller2.email}')
        else:
            self.stdout.write(f'✓ Seller already exists: {seller2.email}')

        self.stdout.write('Creating test categories and products...')
        
        # Get or create a test category
        category, created = Category.objects.get_or_create(
            name='Electronics',
            defaults={
                'slug': 'electronics',
                'description': 'Electronic devices and gadgets',
                'icon': '📱',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'✓ Created category: {category.name}')
        else:
            self.stdout.write(f'✓ Category already exists: {category.name}')

        # Create test products
        products_data = [
            {
                'seller': seller1,
                'name': 'iPhone 14 Pro',
                'description': 'Latest iPhone model with Pro features. Excellent condition, barely used.',
                'price': 999.00,
                'quantity': 1,
                'images': ['https://example.com/iphone1.jpg', 'https://example.com/iphone2.jpg']
            },
            {
                'seller': seller1,
                'name': 'MacBook Air M2',
                'description': 'Brand new MacBook Air with M2 chip. Perfect for students and professionals.',
                'price': 1299.00,
                'quantity': 2,
                'images': ['https://example.com/macbook1.jpg', 'https://example.com/macbook2.jpg']
            },
            {
                'seller': seller2,
                'name': 'Samsung Galaxy S23',
                'description': 'High-end Android phone with amazing camera. Like new condition.',
                'price': 799.00,
                'quantity': 1,
                'images': ['https://example.com/samsung1.jpg', 'https://example.com/samsung2.jpg']
            },
            {
                'seller': seller2,
                'name': 'iPad Pro 12.9"',
                'description': 'Professional tablet perfect for digital art and productivity. Includes Apple Pencil.',
                'price': 1099.00,
                'quantity': 1,
                'images': ['https://example.com/ipad1.jpg', 'https://example.com/ipad2.jpg']
            }
        ]

        created_products = []
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                seller=product_data['seller'],
                defaults={
                    'category': category,
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'quantity': product_data['quantity'],
                    'images': product_data['images'],
                    'is_active': True
                }
            )
            created_products.append(product)
            if created:
                self.stdout.write(f'✓ Created product: {product.name} by {product.seller.email}')
            else:
                self.stdout.write(f'✓ Product already exists: {product.name}')

        self.stdout.write('Creating test chats and messages...')
        
        # Create test chats
        chat1, created = Chat.objects.get_or_create(
            buyer=buyer1,
            seller=seller1,
            product=created_products[0],  # iPhone 14 Pro
            defaults={'is_active': True}
        )
        if created:
            self.stdout.write(f'✓ Created chat between {buyer1.email} and {seller1.email}')
            
            # Add some test messages
            messages_data = [
                {
                    'sender': buyer1,
                    'content': 'Hi! Is this iPhone still available?',
                    'is_read': True
                },
                {
                    'sender': seller1,
                    'content': 'Hello! Yes, it\'s still available. It\'s in excellent condition.',
                    'is_read': True
                },
                {
                    'sender': buyer1,
                    'content': 'Great! Can you tell me more about the battery health?',
                    'is_read': True
                },
                {
                    'sender': seller1,
                    'content': 'The battery health is at 98%. It was purchased just 3 months ago.',
                    'is_read': False
                },
                {
                    'sender': buyer1,
                    'content': 'Perfect! Can we meet somewhere to check it out?',
                    'is_read': False
                }
            ]
            
            for i, msg_data in enumerate(messages_data):
                Message.objects.create(
                    chat=chat1,
                    sender=msg_data['sender'],
                    content=msg_data['content'],
                    message_type='text',
                    is_read=msg_data['is_read']
                )
            
            self.stdout.write(f'✓ Added {len(messages_data)} messages to chat')
        else:
            self.stdout.write('✓ Chat already exists')

        # Create another chat
        chat2, created = Chat.objects.get_or_create(
            buyer=buyer2,
            seller=seller2,
            product=created_products[2],  # Samsung Galaxy S23
            defaults={'is_active': True}
        )
        if created:
            self.stdout.write(f'✓ Created chat between {buyer2.email} and {seller2.email}')
            
            # Add some test messages
            messages_data = [
                {
                    'sender': buyer2,
                    'content': 'Hello! I\'m interested in your Samsung Galaxy S23.',
                    'is_read': True
                },
                {
                    'sender': seller2,
                    'content': 'Hi! Thank you for your interest. What would you like to know?',
                    'is_read': True
                },
                {
                    'sender': buyer2,
                    'content': 'Is it unlocked? And does it come with original accessories?',
                    'is_read': False
                }
            ]
            
            for msg_data in messages_data:
                Message.objects.create(
                    chat=chat2,
                    sender=msg_data['sender'],
                    content=msg_data['content'],
                    message_type='text',
                    is_read=msg_data['is_read']
                )
            
            self.stdout.write(f'✓ Added {len(messages_data)} messages to chat')
        else:
            self.stdout.write('✓ Chat already exists')

        self.stdout.write(self.style.SUCCESS('\n🎉 Test data created successfully!'))
        self.stdout.write('\nTest User Credentials:')
        self.stdout.write('Buyers:')
        self.stdout.write('  - buyer@test.com / testpass123')
        self.stdout.write('  - buyer2@test.com / testpass123')
        self.stdout.write('Sellers:')
        self.stdout.write('  - seller@test.com / testpass123')
        self.stdout.write('  - seller2@test.com / testpass123')
        self.stdout.write(f'\nCreated {len(created_products)} products and {Chat.objects.count()} chats')
        self.stdout.write('\n📋 Next steps:')
        self.stdout.write('1. Run: python manage.py runserver')
        self.stdout.write('2. Test the API endpoints using the test script or API documentation')
        self.stdout.write('3. Login with test credentials to see the chat feature in action')
