from rest_framework.mixins import ListModelMixin
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from orders.models import OrderInfo
from meiduo_admin.serializers.orders_serializer import *
from meiduo_admin.pages import MyPage


class OrderInfoView(ListAPIView):
    queryset = OrderInfo.objects.all().order_by('-create_time')
    serializer_class = OrderInfoSerializer
    pagination_class = MyPage

    def get_queryset(self):
        """实现根据keyword过滤order_id"""
        keyword = self.request.query_params.get("keyword")
        if keyword is not None:
            return self.queryset.filter(order_id__contains=keyword)
        return self.queryset.all()


class OrderInfoDetailView(RetrieveAPIView):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderInfoDetailSerializer
