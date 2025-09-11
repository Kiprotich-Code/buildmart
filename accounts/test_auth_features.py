from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from unittest.mock import patch

User = get_user_model()


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='test@example.com'
        )
        self.password_reset_url = reverse('password-reset')
        self.password_reset_confirm_url = reverse('password-reset-confirm')

    def test_password_reset_request_valid_email(self):
        """Test password reset request with valid email"""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.password_reset_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Password reset email sent successfully', response.data['message'])
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset', mail.outbox[0].subject)

    def test_password_reset_request_invalid_email(self):
        """Test password reset request with invalid email"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.password_reset_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No user found with this email address', str(response.data))

    def test_password_reset_confirm_valid_token(self):
        """Test password reset confirmation with valid token"""
        # Generate valid token
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_password_reset_confirm_invalid_token(self):
        """Test password reset confirmation with invalid token"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        data = {
            'uid': uid,
            'token': 'invalid-token',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_mismatched_passwords(self):
        """Test password reset confirmation with mismatched passwords"""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpassword123'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GoogleOAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.google_oauth_url = reverse('google-oauth')

    @patch('requests.get')
    def test_google_oauth_new_user(self, mock_requests):
        """Test Google OAuth with new user"""
        # Mock Google API response
        mock_response = mock_requests.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '123456789',
            'email': 'newuser@gmail.com',
            'given_name': 'New',
            'family_name': 'User',
            'verified_email': True
        }
        
        data = {'access_token': 'fake-google-token'}
        response = self.client.post(self.google_oauth_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email='newuser@gmail.com').exists())

    @patch('requests.get')
    def test_google_oauth_existing_user(self, mock_requests):
        """Test Google OAuth with existing user"""
        # Create existing user
        existing_user = User.objects.create_user(
            email='existing@gmail.com',
            password='testpass123',
            username='existing@gmail.com'
        )
        
        # Mock Google API response
        mock_response = mock_requests.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': '123456789',
            'email': 'existing@gmail.com',
            'given_name': 'Existing',
            'family_name': 'User',
            'verified_email': True
        }
        
        data = {'access_token': 'fake-google-token'}
        response = self.client.post(self.google_oauth_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'existing@gmail.com')

    @patch('requests.get')
    def test_google_oauth_invalid_token(self, mock_requests):
        """Test Google OAuth with invalid token"""
        # Mock invalid token response
        mock_response = mock_requests.return_value
        mock_response.status_code = 401
        
        data = {'access_token': 'invalid-token'}
        response = self.client.post(self.google_oauth_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid access token', str(response.data))
