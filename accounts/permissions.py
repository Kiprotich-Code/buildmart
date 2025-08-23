from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsSellerUser(BasePermission):
    """
    Permission to only allow seller users to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_seller


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Instance must have a user attribute.
        return obj.user == request.user


class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsSellerOwnerOrAdmin(BasePermission):
    """
    Permission for seller-related objects - only seller owner or admin can access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_admin:
            return True
        # Seller can only access their own data
        return obj.user == request.user and request.user.is_seller


class IsAdminOrSellerOwner(BasePermission):
    """
    Permission that allows admin to manage all sellers, or sellers to manage their own data.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.is_seller
        )
        
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_admin:
            return True
        # Seller can only access their own data
        return obj.user == request.user
