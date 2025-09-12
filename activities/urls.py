from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    # Admin endpoints
    path('admin/activities/', views.AdminActivitiesListView.as_view(), name='admin-activities'),
    path('admin/stats/', views.activity_stats, name='activity-stats'),
    
    # Buyer endpoints
    path('buyer/activities/', views.BuyerActivitiesListView.as_view(), name='buyer-activities'),
    path('buyer/log-view/', views.log_product_view_api, name='log-product-view'),
]
