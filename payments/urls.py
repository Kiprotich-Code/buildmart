from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoostPlanViewSet, BoostViewSet, flutterwave_webhook

router = DefaultRouter()
router.register(r'plans', BoostPlanViewSet, basename='boostplan')
router.register(r'boosts', BoostViewSet, basename='boost')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/flutterwave/', flutterwave_webhook, name='flutterwave_webhook'),
]