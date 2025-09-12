from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from activities.models import RecentActivity
from products.models import Product, Category
from payments.models import BoostPlan, Boost
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample recent activities for testing'

    def handle(self, *args, **options):
        # Create some test users if they don't exist
        admin_user, created = User.objects.get_or_create(
            email='admin@buildmart.com',
            defaults={
                'username': 'admin_buildmart',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True
            }
        )
        if created:
            admin_user.set_password('adminpass123')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.email}')

        buyer_user, created = User.objects.get_or_create(
            email='buyer@test.com',
            defaults={
                'username': 'buyer_test',
                'role': 'user',
                'is_email_verified': True
            }
        )
        if created:
            buyer_user.set_password('buyerpass123')
            buyer_user.save()
            self.stdout.write(f'Created buyer user: {buyer_user.email}')

        seller_user, created = User.objects.get_or_create(
            email='seller@test.com',
            defaults={
                'username': 'seller_test',
                'role': 'seller',
                'is_email_verified': True
            }
        )
        if created:
            seller_user.set_password('sellerpass123')
            seller_user.save()
            self.stdout.write(f'Created seller user: {seller_user.email}')

        # Create sample activities
        activities_data = [
            {
                'action_type': 'user_registration',
                'message': f'New user registered: {buyer_user.email}',
                'user': buyer_user,
                'metadata': {'email': buyer_user.email, 'role': buyer_user.role}
            },
            {
                'action_type': 'user_registration',
                'message': f'New seller registered: {seller_user.email}',
                'user': seller_user,
                'metadata': {'email': seller_user.email, 'role': seller_user.role}
            },
            {
                'action_type': 'payment_processed',
                'message': 'Payment of $50.00 processed for Boost Payment',
                'user': seller_user,
                'metadata': {'amount': '50.00', 'payment_type': 'Boost Payment'}
            },
            {
                'action_type': 'boost_activated',
                'message': 'Boost activated for product: Sample Product',
                'user': seller_user,
                'metadata': {'product_name': 'Sample Product', 'plan_name': 'Premium Plan'}
            },
            {
                'action_type': 'product_approved',
                'message': f'New product listed: Sample Building Material by {seller_user.email}',
                'user': seller_user,
                'metadata': {'product_name': 'Sample Building Material', 'seller_email': seller_user.email}
            },
        ]

        for activity_data in activities_data:
            activity, created = RecentActivity.objects.get_or_create(
                action_type=activity_data['action_type'],
                message=activity_data['message'],
                user=activity_data['user'],
                defaults={
                    'metadata': activity_data.get('metadata', {}),
                    'related_object_id': str(uuid.uuid4())
                }
            )
            if created:
                self.stdout.write(f'Created activity: {activity.action_type} - {activity.message[:50]}...')

        # Create some buyer activities (product views)
        buyer_activities = [
            {
                'action_type': 'product_viewed',
                'message': 'Product viewed: Premium Cement',
                'user': buyer_user,
                'metadata': {
                    'product_name': 'Premium Cement',
                    'price': '25.50',
                    'category': 'Construction Materials'
                }
            },
            {
                'action_type': 'product_viewed',
                'message': 'Product viewed: Steel Rods',
                'user': buyer_user,
                'metadata': {
                    'product_name': 'Steel Rods',
                    'price': '15.75',
                    'category': 'Construction Materials'
                }
            },
        ]

        for activity_data in buyer_activities:
            activity, created = RecentActivity.objects.get_or_create(
                action_type=activity_data['action_type'],
                message=activity_data['message'],
                user=activity_data['user'],
                defaults={
                    'metadata': activity_data.get('metadata', {}),
                    'related_object_id': str(uuid.uuid4())
                }
            )
            if created:
                self.stdout.write(f'Created buyer activity: {activity.action_type} - {activity.message[:50]}...')

        self.stdout.write(self.style.SUCCESS('Successfully created sample activities'))
        self.stdout.write(self.style.SUCCESS(f'Total activities in database: {RecentActivity.objects.count()}'))
