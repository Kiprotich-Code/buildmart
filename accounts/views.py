from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .serializers import (
    UserRegistrationSerializer, LoginSerializer, UserSerializer, 
    ProfileSerializer, SellerSerializer, SellerRegistrationSerializer,
    PasswordChangeSerializer, TokenSerializer, PasswordResetSerializer,
    PasswordResetConfirmSerializer, GoogleOAuthSerializer
)
from .models import Profile, Seller
from .permissions import (
    IsAdminUser, IsSellerUser, IsOwner, IsSellerOwnerOrAdmin, 
    IsAdminOrSellerOwner, IsOwnerOrReadOnly
)

User = get_user_model()


class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """JWT Login endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout endpoint - blacklists refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Current user profile endpoint"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user details"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Update current user details"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete current user account"""
        request.user.delete()
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)


class ProfileDetailView(APIView):
    """User profile management"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's profile"""
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        """Update current user's profile"""
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """Change password endpoint"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin Views
class UserListView(generics.ListAPIView):
    """Admin only - List all users"""
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin only - Manage specific user"""
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()


class ProfileListView(generics.ListAPIView):
    """Admin only - List all profiles"""
    serializer_class = ProfileSerializer
    permission_classes = [IsAdminUser]
    queryset = Profile.objects.all()


# Seller Views
class SellerRegistrationView(APIView):
    """Seller registration endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SellerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            seller = serializer.save()
            refresh = RefreshToken.for_user(seller.user)
            
            return Response({
                'user': UserSerializer(seller.user).data,
                'seller': SellerSerializer(seller).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'Seller registered successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SellerListView(generics.ListAPIView):
    """List sellers - Admin can see all, sellers can see only themselves"""
    serializer_class = SellerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Seller.objects.all()
        elif self.request.user.is_seller:
            return Seller.objects.filter(user=self.request.user)
        else:
            return Seller.objects.none()


class SellerDetailView(APIView):
    """Seller detail management"""
    permission_classes = [IsAdminOrSellerOwner]

    def get_object(self, pk):
        seller = get_object_or_404(Seller, pk=pk)
        self.check_object_permissions(self.request, seller)
        return seller

    def get(self, request, pk):
        """Get seller details"""
        seller = self.get_object(pk)
        serializer = SellerSerializer(seller)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update seller details"""
        seller = self.get_object(pk)
        # Only admin can update verification status
        if 'verification_status' in request.data and not request.user.is_admin:
            return Response({'error': 'Only admin can update verification status'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = SellerSerializer(seller, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete seller (admin only)"""
        if not request.user.is_admin:
            return Response({'error': 'Only admin can delete sellers'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        seller = self.get_object(pk)
        seller.delete()
        return Response({'message': 'Seller deleted successfully'}, status=status.HTTP_200_OK)


class SellerVerificationView(APIView):
    """Admin only - Manage seller verification"""
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        """Verify or reject seller"""
        seller = get_object_or_404(Seller, pk=pk)
        action = request.data.get('action')  # 'verify' or 'reject'
        
        if action == 'verify':
            seller.verification_status = 'verified'
            message = 'Seller verified successfully'
        elif action == 'reject':
            seller.verification_status = 'rejected'
            message = 'Seller rejected'
        else:
            return Response({'error': 'Invalid action. Use "verify" or "reject"'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        seller.save()
        return Response({
            'message': message,
            'seller': SellerSerializer(seller).data
        })


class CurrentSellerView(APIView):
    """Current seller profile endpoint"""
    permission_classes = [IsSellerUser]

    def get(self, request):
        """Get current seller details"""
        try:
            seller = request.user.seller
            serializer = SellerSerializer(seller)
            return Response(serializer.data)
        except Seller.DoesNotExist:
            return Response({'error': 'Seller profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        """Update current seller details"""
        try:
            seller = request.user.seller
            # Sellers cannot update their own verification status
            if 'verification_status' in request.data:
                return Response({'error': 'Cannot update verification status'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            serializer = SellerSerializer(seller, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Seller.DoesNotExist:
            return Response({'error': 'Seller profile not found'}, status=status.HTTP_404_NOT_FOUND)


# Utility Views
class UserStatsView(APIView):
    """Admin only - Get user statistics"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        stats = {
            'total_users': User.objects.count(),
            'total_admins': User.objects.filter(role='admin').count(),
            'total_sellers': User.objects.filter(role='seller').count(),
            'total_regular_users': User.objects.filter(role='user').count(),
            'verified_sellers': Seller.objects.filter(verification_status='verified').count(),
            'pending_sellers': Seller.objects.filter(verification_status='pending').count(),
            'rejected_sellers': Seller.objects.filter(verification_status='rejected').count(),
        }
        return Response(stats)


class VerifyEmailView(APIView):
    """Email verification endpoint (placeholder)"""
    permission_classes = [AllowAny]

    def post(self, request):
        # Placeholder for email verification logic
        # You would implement actual email verification here
        token = request.data.get('token')
        # Verify token and mark user as verified
        return Response({'message': 'Email verification endpoint - implement as needed'}, 
                       status=status.HTTP_200_OK)


class PasswordResetView(APIView):
    """Password reset request endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password reset email sent successfully. Please check your email.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Password reset confirmation endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Password reset successful. You can now login with your new password.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleOAuthView(APIView):
    """Google OAuth authentication endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleOAuthSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.create_or_get_user(serializer.validated_data)
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    },
                    'message': 'Google authentication successful'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': 'Authentication failed',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)