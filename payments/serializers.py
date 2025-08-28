from rest_framework import serializers
from .models import BoostPlan, Boost
from products.serializers import ProductSerializer 

class BoostPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoostPlan
        fields = '__all__'

class BoostSerializer(serializers.ModelSerializer):
    plan = BoostPlanSerializer(read_only=True)
    listing = ProductSerializer(read_only=True)

    class Meta:
        model = Boost
        fields = '__all__'
        read_only_fields = ('user', 'tx_ref', 'start_date', 'end_date', 'is_active', 'payment_status')