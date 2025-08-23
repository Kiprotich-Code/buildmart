from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Seller

User = get_user_model()


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
                 'date_of_birth', 'profile_picture', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_email', 'user_role']


class SellerSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Seller
        fields = ['id', 'user_email', 'shop_name', 'shop_description', 
                 'business_license', 'tax_id', 'state', 'city', 'address', 
                 'union_membership_number', 'verification_status', 'trial_end_date', 
                 'subscription_active', 'subscription_end_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_email', 'verification_status']


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