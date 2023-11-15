from rest_framework import serializers
from app.models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "student", "courses", "quantity",
                  "status", "order_date", "total")
        depth = 1

        read_only_fields = ['total']

    def get_total(self, obj):
        return obj.total
