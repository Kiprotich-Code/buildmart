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

# The resulting URLs will be:
# /api/reports/ - List/Create reports
# /api/reports/{id}/ - Retrieve/Update/Delete specific report
# /api/reports/my_reports/ - Get current user's reports
# /api/reports/pending/ - Get pending reports (admin only)
# /api/reports/{id}/assign/ - Assign report to admin
# 
# /api/flags/ - List/Create flags
# /api/flags/{id}/ - Retrieve/Update/Delete specific flag
# /api/flags/active/ - Get active flags
# /api/flags/critical/ - Get critical flags
# /api/flags/requires_review/ - Get flags requiring manual review
#
# /api/stats/dashboard/ - Get dashboard statistics
# /api/stats/trends/ - Get trends data
# /api/stats/summary/ - Get summary statistics
