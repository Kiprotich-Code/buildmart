from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User management
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/details/', views.ProfileDetailView.as_view(), name='profile-details'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    
    # Admin endpoints
    path('admin/users/', views.UserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/', views.UserDetailView.as_view(), name='admin-user-detail'),
    path('admin/profiles/', views.ProfileListView.as_view(), name='admin-profiles'),
    path('admin/stats/', views.UserStatsView.as_view(), name='admin-stats'),
    
    # Seller endpoints
    path('seller/register/', views.SellerRegistrationView.as_view(), name='seller-register'),
    path('seller/profile/', views.CurrentSellerView.as_view(), name='current-seller'),
    path('sellers/', views.SellerListView.as_view(), name='seller-list'),
    path('sellers/<uuid:pk>/', views.SellerDetailView.as_view(), name='seller-detail'),
    path('sellers/<uuid:pk>/verify/', views.SellerVerificationView.as_view(), name='seller-verify'),
    
    # Include router URLs
    path('', include(router.urls)),
]
