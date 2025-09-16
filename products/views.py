from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Avg, Count, Max
from django.db import transaction
from .models import Category, Product, ProductReview, Boost, ProductImage
from .serializers import (
    CategorySerializer, 
    CategoryListSerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductReviewSerializer,
    BoostSerializer,
    ProductImageSerializer,
    ProductImageUploadSerializer,
    ProductCreateWithImagesSerializer
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
    parser_classes = [MultiPartParser, FormParser]  # Add this to handle file uploads
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'seller__first_name', 'seller__last_name']
    ordering_fields = ['name', 'price', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        Use lightweight serializer for list view and special serializer for create with images.
        """
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create' and 'images' in self.request.data:
            return ProductCreateWithImagesSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        """
        queryset = Product.objects.select_related(
            'category', 
            'seller', 
            'seller__seller'  # Include seller profile for seller_details
        ).prefetch_related('reviews', 'product_images')
        
        # For admin users, allow access to inactive products for modification operations
        if hasattr(self.request, 'user') and self.request.user.is_authenticated and self.request.user.is_staff:
            # Admin users can access all products including inactive ones
            pass
        elif hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # For authenticated non-admin users
            if self.detail:
                # For detail views, allow access to own products (active or inactive) and all active products
                queryset = queryset.filter(
                    Q(seller=self.request.user) | Q(is_active=True)
                )
            else:
                # For list views, filter by active status unless show_inactive=true
                show_inactive = self.request.query_params.get('show_inactive', 'false').lower()
                if show_inactive not in ['true', '1']:
                    queryset = queryset.filter(is_active=True)
        else:
            # For anonymous users, only show active products
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
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a product and log the view activity for buyers.
        """
        instance = self.get_object()
        
        # Log product view for buyers (users with role='user')
        if request.user.is_authenticated and request.user.role == 'user':
            from activities.signals import log_product_view
            log_product_view(request.user, instance)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update a product, handling both regular data and image uploads.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Handle FormData with images
        if 'images' in request.data and hasattr(request.data, 'getlist'):
            return self._update_product_with_images(request, instance, partial=partial)
        
        # Standard update for JSON data
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a product.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def _update_product_with_images(self, request, instance, partial=False):
        """
        Handle product update with image uploads (FormData).
        """
        from django.db import transaction
        from .utils import process_uploaded_images
        
        try:
            with transaction.atomic():
                # Extract form data
                data = {}
                for key in ['name', 'description', 'price', 'quantity', 'category_id']:
                    if key in request.data:
                        data[key] = request.data[key]
                
                # Handle category field mapping
                if 'category_id' in data:
                    data['category'] = data.pop('category_id')
                
                # Get new images and existing images to keep
                new_images = request.FILES.getlist('images') if 'images' in request.FILES else []
                existing_images = request.data.getlist('existing_images') if hasattr(request.data, 'getlist') else []
                
                # Update basic product data
                serializer = ProductSerializer(instance, data=data, partial=partial)
                serializer.is_valid(raise_exception=True)
                product = serializer.save()
                
                # Handle images if any image data is provided
                if new_images or 'existing_images' in request.data:
                    current_images = list(product.product_images.all())
                    
                    # Determine which existing images to keep (by matching URLs)
                    images_to_keep = []
                    if existing_images:
                        for current_img in current_images:
                            img_url = current_img.image.url if current_img.image else ''
                            if img_url in existing_images:
                                images_to_keep.append(current_img)
                    
                    # Remove images that are not in the keep list
                    for current_img in current_images:
                        if current_img not in images_to_keep:
                            current_img.delete()
                    
                    # Update order for kept images and alt texts
                    for idx, img in enumerate(images_to_keep):
                        img.order = idx
                        alt_text_key = f'existing_alt_text_{existing_images.index(img.image.url)}'
                        if alt_text_key in request.data:
                            img.alt_text = request.data[alt_text_key]
                        img.save()
                    
                    # Add new images
                    if new_images:
                        start_order = len(images_to_keep)
                        created_images = process_uploaded_images(new_images, product)
                        
                        # Update order for new images and set alt texts
                        for i, image_obj in enumerate(created_images):
                            image_obj.order = start_order + i
                            alt_text_key = f'alt_text_{i}'
                            alt_text = request.data.get(alt_text_key, '')
                            if alt_text:
                                image_obj.alt_text = alt_text
                            image_obj.save()
                
                # Return updated product data
                updated_serializer = ProductSerializer(product)
                return Response(updated_serializer.data)
                
        except Exception as e:
            return Response(
                {'error': f'Failed to update product: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
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
    def add_review(self, request, pk=None):
        """
        Add a review for a specific product.
        POST /api/products/products/{id}/add_review/
        
        Request body:
        {
            "rating": 5,
            "comment": "Great product!"
        }
        """
        product = self.get_object()
        
        # Check if user is trying to review their own product
        if request.user == product.seller:
            return Response(
                {'error': 'You cannot review your own product'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if product is active
        if not product.is_active:
            return Response(
                {'error': 'Cannot review an inactive product'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has already reviewed this product
        existing_review = ProductReview.objects.filter(
            product=product, 
            user=request.user
        ).first()
        
        if existing_review:
            return Response(
                {'error': 'You have already reviewed this product'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the review
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            
            # Return the created review
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_review(self, request, pk=None):
        """
        Update user's existing review for a specific product.
        PUT/PATCH /api/products/products/{id}/update_review/
        
        Request body:
        {
            "rating": 4,
            "comment": "Updated review comment"
        }
        """
        product = self.get_object()
        
        # Find user's existing review
        try:
            review = ProductReview.objects.get(product=product, user=request.user)
        except ProductReview.DoesNotExist:
            return Response(
                {'error': 'You have not reviewed this product yet'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update the review
        partial = request.method == 'PATCH'
        serializer = ProductReviewSerializer(review, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_review(self, request, pk=None):
        """
        Delete user's existing review for a specific product.
        DELETE /api/products/products/{id}/delete_review/
        """
        product = self.get_object()
        
        # Find user's existing review
        try:
            review = ProductReview.objects.get(product=product, user=request.user)
        except ProductReview.DoesNotExist:
            return Response(
                {'error': 'You have not reviewed this product yet'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Delete the review
        review.delete()
        return Response(
            {'message': 'Review deleted successfully'}, 
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def my_review(self, request, pk=None):
        """
        Get current user's review for a specific product.
        GET /api/products/products/{id}/my_review/
        """
        product = self.get_object()
        
        try:
            review = ProductReview.objects.get(product=product, user=request.user)
            serializer = ProductReviewSerializer(review)
            return Response(serializer.data)
        except ProductReview.DoesNotExist:
            return Response(
                {'error': 'You have not reviewed this product yet'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], 
            parser_classes=[MultiPartParser, FormParser])
    def upload_images(self, request, pk=None):
        """
        Upload multiple images for a product.
        POST /api/products/products/{id}/upload_images/
        
        Form data:
        - images: List of image files
        - alt_texts: Optional list of alt texts (same order as images)
        """
        product = self.get_object()
        
        # Check if user owns the product
        if request.user != product.seller and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only upload images to your own products.")
        
        serializer = ProductImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        images = serializer.validated_data['images']
        alt_texts = serializer.validated_data.get('alt_texts', [])
        
        # Check current image count
        current_count = product.product_images.filter(is_active=True).count()
        if current_count + len(images) > 10:
            return Response({
                'error': f'Cannot upload {len(images)} images. Maximum 10 images per product. Current: {current_count}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        created_images = []
        try:
            with transaction.atomic():
                # Get the next order number
                max_order = product.product_images.aggregate(
                    max_order=Max('order')
                )['max_order'] or -1
                
                for i, image in enumerate(images):
                    alt_text = alt_texts[i] if i < len(alt_texts) else ''
                    
                    product_image = ProductImage.objects.create(
                        product=product,
                        image=image,
                        alt_text=alt_text,
                        order=max_order + i + 1
                    )
                    created_images.append(product_image)
                    
        except Exception as e:
            return Response({
                'error': f'Failed to upload images: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Serialize and return created images
        image_serializer = ProductImageSerializer(created_images, many=True)
        return Response({
            'message': f'Successfully uploaded {len(created_images)} images',
            'images': image_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """
        Get all images for a product.
        GET /api/products/products/{id}/images/
        """
        product = self.get_object()
        images = product.product_images.filter(is_active=True).order_by('order')
        serializer = ProductImageSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reorder_images(self, request, pk=None):
        """
        Reorder product images.
        POST /api/products/products/{id}/reorder_images/
        
        Body: {
            "image_orders": [
                {"id": "image_id", "order": 0},
                {"id": "image_id", "order": 1},
                ...
            ]
        }
        """
        product = self.get_object()
        
        # Check if user owns the product
        if request.user != product.seller and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only reorder images of your own products.")
        
        image_orders = request.data.get('image_orders', [])
        if not image_orders:
            return Response({
                'error': 'image_orders field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                for item in image_orders:
                    image_id = item.get('id')
                    order = item.get('order')
                    
                    if image_id is None or order is None:
                        return Response({
                            'error': 'Each item must have id and order fields'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    try:
                        image = ProductImage.objects.get(id=image_id, product=product)
                        image.order = order
                        image.save()
                    except ProductImage.DoesNotExist:
                        return Response({
                            'error': f'Image with id {image_id} not found'
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
        except Exception as e:
            return Response({
                'error': f'Failed to reorder images: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'message': 'Images reordered successfully'})

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_image(self, request, pk=None):
        """
        Delete a specific product image.
        DELETE /api/products/products/{id}/delete_image/?image_id=<image_id>
        """
        product = self.get_object()
        
        # Check if user owns the product
        if request.user != product.seller and not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete images from your own products.")
        
        image_id = request.query_params.get('image_id')
        if not image_id:
            return Response({
                'error': 'image_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image = ProductImage.objects.get(id=image_id, product=product)
            image.delete()
            return Response({'message': 'Image deleted successfully'})
        except ProductImage.DoesNotExist:
            return Response({
                'error': 'Image not found'
            }, status=status.HTTP_404_NOT_FOUND)
