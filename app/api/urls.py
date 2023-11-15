from django.urls import path
from .views import OrderListView
app_name = 'app_api'
urlpatterns = [
    path('v1/orders', OrderListView.as_view(), name="orders"),
]
