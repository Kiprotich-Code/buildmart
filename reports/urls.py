from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, FlagViewSet, ReportsStatsViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='reports')
router.register(r'flags', FlagViewSet, basename='flags')
router.register(r'stats', ReportsStatsViewSet, basename='reports-stats')

app_name = 'reports'

urlpatterns = [
    path('api/', include(router.urls)),
]