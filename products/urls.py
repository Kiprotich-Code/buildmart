from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet

# Create a default router and register our viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
