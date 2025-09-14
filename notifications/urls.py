from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UserNotificationViewSet, ContactViewSet

router = DefaultRouter()
router.register(r'admin', NotificationViewSet, basename='admin-notifications')
router.register(r'user', UserNotificationViewSet, basename='user-notifications')
router.register(r'contact', ContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
