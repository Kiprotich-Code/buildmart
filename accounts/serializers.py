from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount
from .models import Profile, Seller

User = get_user_model()


class SellerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for seller registration"""
    phone_number = serializers.CharField(max_length=20, required=True)
    
    class Meta:
        model = Seller
        fields = [
            'shop_name', 'shop_description', 'phone_number', 'business_license', 
            'tax_id', 'state', 'city', 'address', 'union_membership_number'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Remove non-digits to count actual digits
        clean_phone = ''.join(char for char in value if char.isdigit())
        
        if len(clean_phone) < 8:
            raise serializers.ValidationError("Phone number must contain at least 8 digits.")
        
        return value.strip()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='user')

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value.lower()
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'user'),
            username=validated_data['email']  # Set username to email for consistency
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email.lower(),
                password=password
            )
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            data['user'] = user
            return data
        else:
            raise serializers.ValidationError('Must include both email and password.')


class ProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user_email', 'user_role', 'full_name', 'phone', 'address', 
                 'profile_picture', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_email', 'user_role']


class SellerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Seller
        fields = ['id', 'user_email', 'shop_name', 'shop_description', 'phone_number',
                 'business_license', 'tax_id', 'state', 'city', 'address', 
                 'union_membership_number', 'verification_status', 'trial_end_date', 
                 'subscription_active', 'subscription_end_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_email', 'verification_status']

    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Remove non-digits to count actual digits
        clean_phone = ''.join(char for char in value if char.isdigit())
        
        if len(clean_phone) < 8:
            raise serializers.ValidationError("Phone number must contain at least 8 digits.")
        
        return value.strip()


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    seller_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_email_verified', 
                 'date_joined', 'last_login', 'profile', 'seller_profile']
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_profile(self, obj):
        # Only return profile for users and admins, not sellers
        if obj.role != 'seller' and hasattr(obj, 'profile'):
            return ProfileSerializer(obj.profile).data
        return None
    
    def get_seller_profile(self, obj):
        # Only return seller profile for sellers
        if obj.role == 'seller' and hasattr(obj, 'seller'):
            return SellerSerializer(obj.seller).data
        return None


class SellerRegistrationSerializer(serializers.ModelSerializer):
    user = UserRegistrationSerializer()

    class Meta:
        model = Seller
        fields = ['user', 'shop_name', 'shop_description', 'business_license', 
                 'tax_id', 'state', 'city', 'address', 'union_membership_number', 
                 'trial_end_date']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'seller'  # Force role to be seller
        
        user_serializer = UserRegistrationSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        seller = Seller.objects.create(user=user, **validated_data)
        return seller


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New password fields didn't match.")
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class TokenSerializer(serializers.Serializer):
    """Serializer for JWT token response"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()

    def validate_email(self, value):
        """Check if user with this email exists"""
        try:
            user = User.objects.get(email__iexact=value)
            if not user.is_active:
                raise serializers.ValidationError("This account is deactivated.")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value.lower()

    def save(self):
        """Send password reset email"""
        email = self.validated_data['email']
        user = User.objects.get(email__iexact=email)
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset link (you can customize this URL based on your frontend)
        reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"
        
        # Send email
        subject = 'Password Reset - BuildMart'
        message = f"""
        Hi {user.first_name or user.email},
        
        You requested a password reset for your BuildMart account.
        
        Click the link below to reset your password:
        {reset_link}
        
        If you didn't request this reset, please ignore this email.
        
        This link will expire in 1 hour.
        
        Best regards,
        BuildMart Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate token and passwords"""
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid user ID.")

        if not default_token_generator.check_token(user, attrs['token']):
            raise serializers.ValidationError("Invalid or expired token.")

        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")

        attrs['user'] = user
        return attrs

    def save(self):
        """Reset the password"""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class GoogleOAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth authentication"""
    access_token = serializers.CharField()
    
    def validate_access_token(self, access_token):
        """Validate Google access token"""
        import requests
        
        try:
            # Verify token with Google
            google_user_info_url = f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}'
            response = requests.get(google_user_info_url, timeout=10)
            
            if response.status_code != 200:
                raise serializers.ValidationError("Invalid or expired access token.")
                
            user_data = response.json()
            
            if 'email' not in user_data:
                raise serializers.ValidationError("Email not found in Google account.")
                
            return user_data
            
        except requests.RequestException as e:
            raise serializers.ValidationError(f"Failed to verify token with Google: {str(e)}")
    
    def create_or_get_user(self, validated_data):
        """Create or get user from Google OAuth data"""
        user_data = validated_data['access_token']
        
        email = user_data['email']
        first_name = user_data.get('given_name', '')
        last_name = user_data.get('family_name', '')
        google_id = user_data.get('id')
        
        try:
            # Check if user already exists
            user = User.objects.get(email__iexact=email)
            
            # Check if this Google account is already linked
            try:
                social_account = SocialAccount.objects.get(
                    user=user,
                    provider='google',
                    uid=google_id
                )
            except SocialAccount.DoesNotExist:
                # Link Google account to existing user
                SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    uid=google_id,
                    extra_data=user_data
                )
                
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                email=email,
                username=email,
                first_name=first_name,
                last_name=last_name,
                is_email_verified=True,  # Google emails are verified
                role='user'
            )
            
            # Create social account
            SocialAccount.objects.create(
                user=user,
                provider='google',
                uid=google_id,
                extra_data=user_data
            )
        
        return user