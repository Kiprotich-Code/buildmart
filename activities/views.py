from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import RecentActivity
from .serializers import RecentActivitySerializer, AdminActivitySerializer, BuyerActivitySerializer
from .signals import log_product_view

class AdminActivitiesListView(generics.ListAPIView):
    """
    API endpoint for admins to view all recent activities
    """
    serializer_class = AdminActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only allow admins to access this endpoint
        if not (self.request.user.is_admin or self.request.user.is_superuser):
            return RecentActivity.objects.none()
        
        # Get admin-relevant activities (exclude product views by buyers)
        admin_activity_types = [
            'user_registration',
            'payment_approved',
            'boost_activated',
            'product_flagged',
            'product_approved',
            'user_suspended', 
            'user_reactivated',
            'seller_verified',
            'payment_processed'
        ]
        
        queryset = RecentActivity.objects.filter(
            action_type__in=admin_activity_types
        ).select_related('user')
        
        # Optional filtering by time period
        days = self.request.query_params.get('days', None)
        if days:
            try:
                days_int = int(days)
                since = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(created_at__gte=since)
            except ValueError:
                pass
        
        # Optional filtering by activity type
        action_type = self.request.query_params.get('action_type', None)
        if action_type and action_type in [choice[0] for choice in RecentActivity.ACTION_TYPES]:
            queryset = queryset.filter(action_type=action_type)
        
        return queryset[:50]  # Limit to 50 most recent

class BuyerActivitiesListView(generics.ListAPIView):
    """
    API endpoint for buyers to view their recent product views
    """
    serializer_class = BuyerActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only allow buyers (users) to access this endpoint
        if self.request.user.role != 'user':
            return RecentActivity.objects.none()
        
        # Get only product view activities for this specific user
        return RecentActivity.objects.filter(
            user=self.request.user,
            action_type__in=['product_viewed', 'material_viewed']
        )[:20]  # Limit to 20 most recent views

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def log_product_view_api(request):
    """
    API endpoint to log when a buyer views a product
    """
    if request.user.role != 'user':  # Only for buyers
        return Response(
            {'error': 'Only buyers can log product views'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    product_id = request.data.get('product_id')
    if not product_id:
        return Response(
            {'error': 'product_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from products.models import Product
        product = Product.objects.get(id=product_id, is_active=True)
        log_product_view(request.user, product)
        
        return Response(
            {'message': 'Product view logged successfully'}, 
            status=status.HTTP_201_CREATED
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to log product view'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def activity_stats(request):
    """
    API endpoint to get activity statistics for admins
    """
    if not (request.user.is_admin or request.user.is_superuser):
        return Response(
            {'error': 'Admin access required'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get statistics for the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    stats = {}
    for action_type, display_name in RecentActivity.ACTION_TYPES:
        if action_type not in ['product_viewed', 'material_viewed']:  # Exclude buyer activities
            count = RecentActivity.objects.filter(
                action_type=action_type,
                created_at__gte=thirty_days_ago
            ).count()
            stats[action_type] = {
                'display_name': display_name,
                'count': count
            }
    
    # Get total activities today
    today = timezone.now().date()
    today_count = RecentActivity.objects.filter(
        created_at__date=today
    ).exclude(
        action_type__in=['product_viewed', 'material_viewed']
    ).count()
    
    return Response({
        'stats': stats,
        'today_total': today_count,
        'period': '30 days'
    })
