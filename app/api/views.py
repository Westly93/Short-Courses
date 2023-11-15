from rest_framework.generics import ListAPIView
from .serializers import OrderSerializer
from app.models import Order


class OrderListView(ListAPIView):
    queryset = Order.objects.filter(status="paid")
    serializer_class = OrderSerializer
