from rest_framework.generics import GenericAPIView, UpdateAPIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from orders.models import OrderInfo
from meiduo_admin.serializers.orders_serializer import *
from meiduo_admin.pages import MyPage
from rest_framework.permissions import IsAdminUser, BasePermission


class MyAddOrderInfo(BasePermission):
    """
    自定权限，有没有对OrderInfo这样表对"增加"权限
    """

    def has_permission(self, request, view):
        return request.user and request.user.has_perm("orders.add_orderinfo")


class OrderInfoView(ListAPIView):
    queryset = OrderInfo.objects.all().order_by('-create_time')
    serializer_class = OrderInfoSerializer
    pagination_class = MyPage

    permission_classes = [MyAddOrderInfo]

    def get_queryset(self):
        """实现根据keyword过滤order_id"""
        keyword = self.request.query_params.get("keyword")
        if keyword is not None:
            return self.queryset.filter(order_id__contains=keyword)
        return self.queryset.all()


class OrderInfoDetailView(RetrieveAPIView, UpdateAPIView):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderInfoDetailSerializer
