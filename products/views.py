from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Category, Product, ProductReview, Boost
from .serializers import (
    CategorySerializer, 
    CategoryListSerializer,
    ProductSerializer,
    ProductReviewSerializer,
    BoostSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories.
    
    Provides standard CRUD operations:
    - GET /api/products/categories/ - List all categories (public)
    - POST /api/products/categories/ - Create a new category (authenticated users)
    - GET /api/products/categories/{id}/ - Retrieve a specific category (public)
    - PUT /api/products/categories/{id}/ - Update a category (authenticated users)
    - PATCH /api/products/categories/{id}/ - Partial update a category (authenticated users)
    - DELETE /api/products/categories/{id}/ - Delete a category (authenticated users)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        Use lightweight serializer for list view.
        """
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        """
        queryset = Category.objects.all()
        
        # Filter by active status (default to active only)
        show_inactive = self.request.query_params.get('show_inactive', 'false').lower()
        if show_inactive not in ['true', '1']:
            queryset = queryset.filter(is_active=True)
            
        # Filter by parent category
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def subcategories(self, request):
        """
        Get all subcategories (categories with parent).
        GET /api/products/categories/subcategories/
        """
        subcategories = self.get_queryset().filter(parent__isnull=False)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def root_categories(self, request):
        """
        Get all root categories (categories without parent).
        GET /api/products/categories/root_categories/
        """
        root_categories = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """
        Get all direct children of a specific category.
        GET /api/products/categories/{id}/children/
        """
        category = self.get_object()
        children = category.subcategories.filter(is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """
        Get all products in a specific category.
        GET /api/products/categories/{id}/products/
        """
        category = self.get_object()
        products = category.products.filter(is_active=True)
        
        # Apply pagination if needed
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
