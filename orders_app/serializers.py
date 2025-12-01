from rest_framework import serializers
from .models import Order

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = []

class OrderSerializer(serializers.ModelSerializer):
    tenantId = serializers.CharField(source='tenant_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    totalCents = serializers.IntegerField(source='total_cents', required=False, allow_null=True)

    class Meta:
        model = Order
        fields = ['id', 'tenantId', 'status', 'version', 'totalCents', 'createdAt', 'updatedAt']

class ConfirmSerializer(serializers.Serializer):
    totalCents = serializers.IntegerField(min_value=0)
