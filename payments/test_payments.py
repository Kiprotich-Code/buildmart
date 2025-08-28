import uuid
from datetime import timedelta
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from payments.models import BoostPlan, Boost
from products.models import Product, Category
from payments.serializers import BoostPlanSerializer, BoostSerializer

User = get_user_model()

class PaymentsTests(TestCase):
    def setUp(self):
        """
        Set up test data: user, product, and boost plans.
        Ensure Product model exists in products/models.py with name, owner, status fields.
        Ensure ProductSerializer exists in products/serializers.py.
        Uses settings.AUTH_USER_MODEL (accounts.CustomUser) for user creation.
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)

        # Create a category first
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        # Create a product
        self.product = Product.objects.create(
            name="Test Product",
            seller=self.user,
            category=self.category,
            price=1000.00,
            quantity=10,
            is_active=True
        )

        # Create boost plans
        self.plan_basic = BoostPlan.objects.create(
            name="Basic Boost",
            price=2000.00,
            duration_days=7,
            features=["2x visibility", "Basic analytics"]
        )
        self.plan_premium = BoostPlan.objects.create(
            name="Premium Boost",
            price=5000.00,
            duration_days=14,
            features=["5x visibility", "Advanced analytics"]
        )

        # URLs
        self.plans_url = reverse('boostplan-list')
        self.boosts_url = reverse('boost-list')
        self.initiate_boost_url = reverse('boost-initiate')
        self.webhook_url = reverse('flutterwave_webhook')

    def test_test_file_discovery(self):
        """Simple test to ensure the test file is being discovered."""
        self.assertTrue(True, "Test file was not discovered by Django test runner.")

    def test_boost_plan_model(self):
        """Test BoostPlan model creation and string representation."""
        plan = BoostPlan.objects.create(
            name="Test Plan",
            price=1000.00,
            duration_days=5,
            features=["Test feature"]
        )
        self.assertEqual(str(plan), "Test Plan")
        self.assertEqual(plan.price, 1000.00)
        self.assertEqual(plan.duration_days, 5)
        self.assertEqual(plan.features, ["Test feature"])

    def test_boost_model(self):
        """Test Boost model creation, string representation, and save logic."""
        boost = Boost.objects.create(
            user=self.user,
            listing=self.product,
            plan=self.plan_basic,
            tx_ref=str(uuid.uuid4()),
            payment_status='pending'
        )
        self.assertEqual(str(boost), f"{self.plan_basic.name} for {self.product.name} by {self.user.username}")
        self.assertFalse(boost.is_active)
        self.assertIsNone(boost.start_date)
        self.assertIsNone(boost.end_date)

        # Test save logic for paid status
        boost.payment_status = 'paid'
        boost.save()
        self.assertTrue(boost.is_active)
        self.assertIsNotNone(boost.start_date)
        self.assertEqual(
            boost.end_date,
            boost.start_date + timedelta(days=self.plan_basic.duration_days)
        )

    def test_boost_plan_serializer(self):
        """Test BoostPlanSerializer serialization."""
        serializer = BoostPlanSerializer(self.plan_basic)
        data = serializer.data
        self.assertEqual(data['name'], "Basic Boost")
        self.assertEqual(float(data['price']), 2000.00)
        self.assertEqual(data['duration_days'], 7)
        self.assertEqual(data['features'], ["2x visibility", "Basic analytics"])

    def test_boost_serializer(self):
        """Test BoostSerializer serialization."""
        boost = Boost.objects.create(
            user=self.user,
            listing=self.product,
            plan=self.plan_basic,
            tx_ref=str(uuid.uuid4()),
            payment_status='pending'
        )
        serializer = BoostSerializer(boost)
        data = serializer.data
        self.assertEqual(data['payment_status'], 'pending')
        self.assertEqual(data['plan']['name'], "Basic Boost")
        self.assertEqual(data['listing']['name'], "Test Product")
        self.assertEqual(data['user'], self.user.id)

    def test_get_boost_plans(self):
        """Test GET /api/payments/plans/ endpoint."""
        response = self.client.get(self.plans_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], "Basic Boost")
        self.assertEqual(response.data[1]['name'], "Premium Boost")

    def test_get_user_boosts(self):
        """Test GET /api/payments/boosts/ endpoint (user-specific)."""
        Boost.objects.create(
            user=self.user,
            listing=self.product,
            plan=self.plan_basic,
            tx_ref=str(uuid.uuid4()),
            payment_status='pending'
        )
        other_user = User.objects.create_user(
            username='other',
            password='otherpass',
            email='other@example.com'
        )
        Boost.objects.create(
            user=other_user,
            listing=self.product,
            plan=self.plan_premium,
            tx_ref=str(uuid.uuid4()),
            payment_status='pending'
        )

        response = self.client.get(self.boosts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only user's boosts
        self.assertEqual(response.data[0]['plan']['name'], "Basic Boost")

    @patch('requests.post')
    def test_initiate_boost_success(self, mock_post):
        """Test POST /api/payments/boosts/initiate/ with successful Flutterwave response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {'link': 'https://checkout.flutterwave.com/test123'}
        }
        mock_post.return_value = mock_response

        data = {
            'listing_id': self.product.id,
            'plan_id': self.plan_basic.id
        }
        response = self.client.post(self.initiate_boost_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_link', response.data)
        self.assertIn('boost_id', response.data)

        boost = Boost.objects.get(id=response.data['boost_id'])
        self.assertEqual(boost.payment_status, 'pending')
        self.assertEqual(boost.user, self.user)
        self.assertEqual(boost.listing, self.product)
        self.assertEqual(boost.plan, self.plan_basic)

    def test_initiate_boost_invalid_product(self):
        """Test POST /api/payments/boosts/initiate/ with invalid product."""
        data = {
            'listing_id': 999,  # Non-existent
            'plan_id': self.plan_basic.id
        }
        response = self.client.post(self.initiate_boost_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Listing not found or not owned by you')

    def test_initiate_boost_invalid_plan(self):
        """Test POST /api/payments/boosts/initiate/ with invalid plan."""
        data = {
            'listing_id': self.product.id,
            'plan_id': 999  # Non-existent
        }
        response = self.client.post(self.initiate_boost_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid plan')

    @patch('requests.post')
    def test_initiate_boost_flutterwave_failure(self, mock_post):
        """Test POST /api/payments/boosts/initiate/ with Flutterwave API failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        data = {
            'listing_id': self.product.id,
            'plan_id': self.plan_basic.id
        }
        response = self.client.post(self.initiate_boost_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Failed to initialize payment', response.data['error'])
        self.assertFalse(Boost.objects.filter(listing=self.product).exists())  # Cleanup on failure

    @patch('requests.get')
    def test_flutterwave_webhook_success(self, mock_get):
        """Test POST /api/payments/webhook/flutterwave/ with successful payment verification."""
        boost = Boost.objects.create(
            user

=self.user,
            listing=self.product,
            plan=self.plan_basic,
            tx_ref=str(uuid.uuid4()),
            payment_status='pending'
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'status': 'successful',
                'amount': 2000.00,
                'currency': 'NGN',
                'tx_ref': boost.tx_ref
            }
        }
        mock_get.return_value = mock_response

        payload = {
            'event': 'charge.completed',
            'data': {
                'id': 123,
                'tx_ref': boost.tx_ref,
                'amount': 2000.00,
                'currency': 'NGN'
            }
        }
        response = self.client.post(self.webhook_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        boost.refresh_from_db()
        self.assertEqual(boost.payment_status, 'paid')
        self.assertTrue(boost.is_active)
        self.assertIsNotNone(boost.start_date)
        self.assertIsNotNone(boost.end_date)

    @patch('requests.get')
    def test_flutterwave_webhook_invalid_transaction(self, mock_get):
        """Test webhook with invalid transaction verification."""
        boost = Boost.objects.create(
            user=self.user,
            listing=self.product,
            plan=self.plan_basic,
            tx_ref=str(uuid.uuid4()),
            payment_status='pending'
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'status': 'failed',
                'amount': 2000.00,
                'currency': 'NGN',
                'tx_ref': boost.tx_ref
            }
        }
        mock_get.return_value = mock_response

        payload = {
            'event': 'charge.completed',
            'data': {
                'id': 123,
                'tx_ref': boost.tx_ref
            }
        }
        response = self.client.post(self.webhook_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        boost.refresh_from_db()
        self.assertEqual(boost.payment_status, 'failed')
        self.assertFalse(boost.is_active)

    def test_flutterwave_webhook_non_charge_event(self):
        """Test webhook with non-charge.completed event."""
        payload = {
            'event': 'other.event',
            'data': {'id': 123}
        }
        response = self.client.post(self.webhook_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No boosts created or modified
        self.assertFalse(Boost.objects.exists())

    def test_unauthenticated_access(self):
        """Test that endpoints require authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.plans_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(self.initiate_boost_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_boost_extension_logic(self):
        """Test boost extension when product already has an active boost."""
        # Create an active boost
        start_date = timezone.now()
        active_boost = Boost.objects.create(
            user=self.user,
            listing=self.product,
            plan=self.plan_basic,
            tx_ref=str(uuid.uuid4()),
            payment_status='paid',
            start_date=start_date,
            end_date=start_date + timedelta(days=self.plan_basic.duration_days),
            is_active=True
        )

        # Initiate a new boost
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'status': 'success',
                'data': {'link': 'https://checkout.flutterwave.com/test456'}
            }
            mock_post.return_value = mock_response

            data = {
                'listing_id': self.product.id,
                'plan_id': self.plan_premium.id
            }
            response = self.client.post(self.initiate_boost_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            new_boost = Boost.objects.get(id=response.data['boost_id'])
            self.assertEqual(new_boost.payment_status, 'pending')

            # Simulate webhook for new boost
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'data': {
                        'status': 'successful',
                        'amount': 5000.00,
                        'currency': 'NGN',
                        'tx_ref': new_boost.tx_ref
                    }
                }
                mock_get.return_value = mock_response

                payload = {
                    'event': 'charge.completed',
                    'data': {
                        'id': 456,
                        'tx_ref': new_boost.tx_ref,
                        'amount': 5000.00,
                        'currency': 'NGN'
                    }
                }
                response = self.client.post(self.webhook_url, payload, format='json')
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                new_boost.refresh_from_db()
                self.assertEqual(new_boost.payment_status, 'paid')
                self.assertEqual(new_boost.start_date, active_boost.end_date)
                self.assertEqual(
                    new_boost.end_date,
                    active_boost.end_date + timedelta(days=self.plan_premium.duration_days)
                )