from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Report, Flag
from products.models import Product, Category
from accounts.models import Seller
from chats.models import Chat, Message

User = get_user_model()


class ReportModelTest(TestCase):
    """Test Report model functionality"""
    
    def setUp(self):
        # Create test users
        self.reporter = User.objects.create_user(
            email='reporter@test.com',
            username='reporter',
            password='testpass123',
            role='user'
        )
        
        self.seller_user = User.objects.create_user(
            email='seller@test.com',
            username='seller',
            password='testpass123',
            role='seller'
        )
        
        # Create a test product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            seller=self.seller_user,
            category=self.category,
            name='Test Product',
            description='Test description',
            price=100.00,
            quantity=10
        )
    
    def test_report_creation(self):
        """Test creating a report"""
        content_type = ContentType.objects.get_for_model(Product)
        
        report = Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.reporter,
            reported_user=self.seller_user,
            reason='fake_listing',
            description='This is a fake listing'
        )
        
        self.assertTrue(report.id.startswith('rpt_'))
        self.assertEqual(report.type, 'listing')
        self.assertEqual(report.status, 'pending')  # Default status
        self.assertEqual(report.priority, 'medium')  # Default priority
        self.assertEqual(report.reporter, self.reporter)
        self.assertEqual(report.reported_user, self.seller_user)
    
    def test_report_properties(self):
        """Test report model properties"""
        content_type = ContentType.objects.get_for_model(Product)
        
        report = Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.reporter,
            reported_user=self.seller_user,
            reason='fake_listing',
            description='This is a fake listing'
        )
        
        self.assertEqual(report.reported_item_id, str(self.product.id))
        self.assertEqual(report.reported_item_title, self.product.name)
        self.assertEqual(report.reporter_email, self.reporter.email)
    
    def test_custom_id_generation(self):
        """Test custom ID generation for reports"""
        content_type = ContentType.objects.get_for_model(Product)
        
        # Create first report
        report1 = Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.reporter,
            reason='fake_listing',
            description='First report'
        )
        
        # Create second report
        report2 = Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.reporter,
            reason='spam',
            description='Second report'
        )
        
        self.assertEqual(report1.id, 'rpt_001')
        self.assertEqual(report2.id, 'rpt_002')


class FlagModelTest(TestCase):
    """Test Flag model functionality"""
    
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='testpass123',
            role='admin'
        )
        
        self.seller_user = User.objects.create_user(
            email='seller@test.com',
            username='seller',
            password='testpass123',
            role='seller'
        )
        
        # Create a test product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            seller=self.seller_user,
            category=self.category,
            name='Test Product',
            description='Test description',
            price=100.00,
            quantity=10
        )
    
    def test_flag_creation(self):
        """Test creating a flag"""
        content_type = ContentType.objects.get_for_model(Product)
        
        flag = Flag.objects.create(
            item_type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            flag_type='automated',
            reason='Price significantly below market average',
            severity='high',
            flagged_by='System'
        )
        
        self.assertTrue(flag.id.startswith('flg_'))
        self.assertEqual(flag.item_type, 'listing')
        self.assertEqual(flag.status, 'active')  # Default status
        self.assertEqual(flag.severity, 'high')
        self.assertEqual(flag.flagged_by, 'System')
    
    def test_flag_properties(self):
        """Test flag model properties"""
        content_type = ContentType.objects.get_for_model(Product)
        
        flag = Flag.objects.create(
            item_type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            flag_type='automated',
            reason='Suspicious activity detected',
            severity='critical'
        )
        
        self.assertEqual(flag.item_id, str(self.product.id))
        self.assertEqual(flag.item_title, self.product.name)


class ReportAPITest(APITestCase):
    """Test Report API endpoints"""
    
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='testpass123',
            role='user'
        )
        
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='testpass123'
        )
        
        self.seller_user = User.objects.create_user(
            email='seller@test.com',
            username='seller',
            password='testpass123',
            role='seller'
        )
        
        # Create test product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            seller=self.seller_user,
            category=self.category,
            name='Test Product',
            description='Test description',
            price=100.00,
            quantity=10
        )
        
        # URLs
        self.reports_url = '/api/reports/api/reports/'
        self.stats_url = '/api/reports/api/stats/dashboard/'
    
    def get_user_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_create_report_authenticated(self):
        """Test creating a report as authenticated user"""
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'type': 'listing',
            'reported_item_type': 'listing',
            'reported_item_object_id': str(self.product.id),
            'reason': 'fake_listing',
            'description': 'This listing appears to be fake',
            'evidence_urls': ['http://example.com/evidence.jpg']
        }
        
        response = self.client.post(self.reports_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that report was created
        report = Report.objects.get(id=response.data['id'])
        self.assertEqual(report.reporter, self.user)
        self.assertEqual(report.reported_user, self.seller_user)
        self.assertEqual(report.type, 'listing')
        self.assertEqual(report.reason, 'fake_listing')
    
    def test_create_report_unauthenticated(self):
        """Test creating a report without authentication"""
        data = {
            'type': 'listing',
            'reported_item_type': 'listing',
            'reported_item_object_id': str(self.product.id),
            'reason': 'fake_listing',
            'description': 'This listing appears to be fake'
        }
        
        response = self.client.post(self.reports_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_reports_user(self):
        """Test listing reports as regular user (should only see own reports)"""
        # Create reports
        content_type = ContentType.objects.get_for_model(Product)
        
        # User's own report
        Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.user,
            reason='fake_listing',
            description='My report'
        )
        
        # Another user's report
        Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.admin,
            reason='spam',
            description='Admin report'
        )
        
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.reports_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response should be a list for DRF ViewSet without pagination
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)  # Should only see own report
        else:
            self.assertEqual(len(response.data), 1)  # Should only see own report
    
    def test_list_reports_admin(self):
        """Test listing reports as admin (should see all reports)"""
        # Create reports
        content_type = ContentType.objects.get_for_model(Product)
        
        Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.user,
            reason='fake_listing',
            description='User report'
        )
        
        Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.admin,
            reason='spam',
            description='Admin report'
        )
        
        token = self.get_user_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.reports_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response should be a list for DRF ViewSet without pagination
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)  # Should see all reports
        else:
            self.assertEqual(len(response.data), 2)  # Should see all reports
    
    def test_update_report_admin_only(self):
        """Test that only admins can update reports"""
        content_type = ContentType.objects.get_for_model(Product)
        
        report = Report.objects.create(
            type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            reporter=self.user,
            reason='fake_listing',
            description='Test report'
        )
        
        # Try to update as regular user
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'status': 'resolved'}
        response = self.client.patch(f'{self.reports_url}{report.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to update as admin
        token = self.get_user_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(f'{self.reports_url}{report.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that report was updated
        report.refresh_from_db()
        self.assertEqual(report.status, 'resolved')
    
    def test_stats_endpoint_admin_only(self):
        """Test that stats endpoint is admin-only"""
        # Try as regular user
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try as admin
        token = self.get_user_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        expected_keys = [
            'total_reports', 'pending_reports', 'resolved_reports',
            'dismissed_reports', 'total_flags', 'active_flags',
            'critical_flags', 'avg_resolution_time'
        ]
        for key in expected_keys:
            self.assertIn(key, response.data)


class FlagAPITest(APITestCase):
    """Test Flag API endpoints"""
    
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            password='testpass123',
            role='user'
        )
        
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            username='admin',
            password='testpass123'
        )
        
        # Create test product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.seller_user = User.objects.create_user(
            email='seller@test.com',
            username='seller',
            password='testpass123',
            role='seller'
        )
        
        self.product = Product.objects.create(
            seller=self.seller_user,
            category=self.category,
            name='Test Product',
            description='Test description',
            price=100.00,
            quantity=10
        )
        
        # URLs
        self.flags_url = '/api/reports/api/flags/'
    
    def get_user_token(self, user):
        """Helper method to get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_flags_admin_only(self):
        """Test that flag endpoints are admin-only"""
        # Try as regular user
        token = self.get_user_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.flags_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try as admin
        token = self.get_user_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.flags_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_flag_admin(self):
        """Test creating a flag as admin"""
        token = self.get_user_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'item_type': 'listing',
            'flagged_item_type': 'listing',
            'flagged_item_object_id': str(self.product.id),
            'flag_type': 'automated',
            'reason': 'Suspicious pricing detected',
            'severity': 'high',
            'flagged_by': 'System'
        }
        
        response = self.client.post(self.flags_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that flag was created
        flag = Flag.objects.get(id=response.data['id'])
        self.assertEqual(flag.item_type, 'listing')
        self.assertEqual(flag.severity, 'high')
    
    def test_update_flag_admin(self):
        """Test updating a flag as admin"""
        content_type = ContentType.objects.get_for_model(Product)
        
        flag = Flag.objects.create(
            item_type='listing',
            content_type=content_type,
            object_id=str(self.product.id),
            flag_type='automated',
            reason='Test flag',
            severity='medium'
        )
        
        token = self.get_user_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'status': 'resolved', 'admin_notes': 'Reviewed and resolved'}
        response = self.client.patch(f'{self.flags_url}{flag.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that flag was updated
        flag.refresh_from_db()
        self.assertEqual(flag.status, 'resolved')
        self.assertEqual(flag.admin_notes, 'Reviewed and resolved')
        self.assertIsNotNone(flag.reviewed_at)
        self.assertEqual(flag.reviewed_by, self.admin)
