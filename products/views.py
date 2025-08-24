from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Q, Avg, Count
from .models import Category, Product, ProductReview, Boost
from .serializers import (
    CategorySerializer, 
    CategoryListSerializer,
    ProductSerializer,
    ProductListSerializer,
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


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.
    
    Provides standard CRUD operations:
    - GET /api/products/products/ - List all products (public)
    - POST /api/products/products/ - Create a new product (authenticated sellers)
    - GET /api/products/products/{id}/ - Retrieve a specific product (public)
    - PUT /api/products/products/{id}/ - Update a product (owner or admin)
    - PATCH /api/products/products/{id}/ - Partial update a product (owner or admin)
    - DELETE /api/products/products/{id}/ - Delete a product (owner or admin)
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'seller__first_name', 'seller__last_name']
    ordering_fields = ['name', 'price', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        Use lightweight serializer for list view.
        """
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        """
        queryset = Product.objects.select_related('category', 'seller').prefetch_related('reviews')
        
        # Filter by active status (default to active only)
        show_inactive = self.request.query_params.get('show_inactive', 'false').lower()
        if show_inactive not in ['true', '1']:
            queryset = queryset.filter(is_active=True)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by seller
        seller_id = self.request.query_params.get('seller')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by availability (quantity > 0)
        in_stock = self.request.query_params.get('in_stock', 'false').lower()
        if in_stock in ['true', '1']:
            queryset = queryset.filter(quantity__gt=0)
        
        # Filter by boosted products
        boosted_only = self.request.query_params.get('boosted_only', 'false').lower()
        if boosted_only in ['true', '1']:
            queryset = queryset.filter(is_boosted=True)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set the seller to the current user when creating a product.
        """
        serializer.save(seller=self.request.user)
    
    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    def check_object_permissions(self, request, obj):
        """
        Check if the user has permission to modify this product.
        Only the seller who owns the product or an admin can modify it.
        """
        super().check_object_permissions(request, obj)
        if self.action in ['update', 'partial_update', 'destroy']:
            if request.user != obj.seller and not request.user.is_staff:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only modify your own products.")
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured (boosted) products.
        GET /api/products/products/featured/
        """
        featured_products = self.get_queryset().filter(is_boosted=True)
        
        page = self.paginate_queryset(featured_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get popular products (based on review count and rating).
        GET /api/products/products/popular/
        """
        popular_products = self.get_queryset().annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).filter(
            review_count__gte=3,
            avg_rating__gte=4.0
        ).order_by('-avg_rating', '-review_count')
        
        page = self.paginate_queryset(popular_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(popular_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_products(self, request):
        """
        Get products owned by the current user.
        GET /api/products/products/my_products/
        """
        my_products = Product.objects.filter(seller=request.user)
        
        page = self.paginate_queryset(my_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(my_products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        Get all reviews for a specific product.
        GET /api/products/products/{id}/reviews/
        """
        product = self.get_object()
        reviews = product.reviews.order_by('-created_at')
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def start_chat(self, request, pk=None):
        """
        Start a chat about this product with the seller.
        POST /api/products/products/{id}/start_chat/
        """
        product = self.get_object()
        
        # Check if user is trying to chat with themselves
        if request.user == product.seller:
            return Response(
                {'error': 'You cannot start a chat with yourself'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if product is active
        if not product.is_active:
            return Response(
                {'error': 'Cannot start chat for inactive product'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import here to avoid circular imports
        from chats.models import Chat
        from chats.serializers import ChatSerializer
        
        # Get or create chat
        chat, created = Chat.objects.get_or_create(
            buyer=request.user,
            seller=product.seller,
            product=product,
            defaults={'is_active': True}
        )
        
        # If chat exists but was inactive, reactivate it
        if not created and not chat.is_active:
            chat.is_active = True
            chat.save()
        
        # Serialize and return chat
        chat_serializer = ChatSerializer(chat, context={'request': request})
        
        return Response({
            'message': 'Chat started successfully' if created else 'Chat already exists',
            'chat': chat_serializer.data,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a product.
        POST /api/products/products/{id}/toggle_active/
        """
        product = self.get_object()
        
        # Check if user owns the product
        if request.user != product.seller and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only toggle your own products.")
        
        product.is_active = not product.is_active
        product.save()
        
        serializer = self.get_serializer(product)
        return Response({
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully',
            'product': serializer.data
        })
