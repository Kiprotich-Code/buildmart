from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UserNotificationViewSet

router = DefaultRouter()
router.register(r'admin', NotificationViewSet, basename='admin-notifications')
router.register(r'user', UserNotificationViewSet, basename='user-notifications')

urlpatterns = [
    path('', include(router.urls)),
]
