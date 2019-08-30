from datetime import timedelta
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from users.models import User
from orders.models import OrderInfo
from goods.models import GoodsVisitCount
from django.utils import timezone
from django.conf import settings
import pytz
from meiduo_admin.serializers.home_serializer import *
from rest_framework.permissions import IsAdminUser


class HomeView(ViewSet):
    permission_classes = [IsAdminUser]
    # 获取当天零点时间（全局变量）
    cur_0_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE)).\
        replace(hour=0, minute=0, second=0,microsecond=0)

    # 用户总数
    # GET
    # statistical/total_count/
    @action(methods=['get'], detail=False)
    def total_count(self, request):
        # 1.统计用户总数
        count = User.objects.all().count()
        # 2.构建响应数据
        shanghai_tz = pytz.timezone(settings.TIME_ZONE)
        shanghai_now_time = timezone.now().astimezone(tz=shanghai_tz)
        date = shanghai_now_time.date()

        return Response({
            "count": count,
            "date": date
        })

    # 日新增用户
    # GET
    # statistical/day_increment/
    @action(methods=['get'], detail=False)
    def day_increment(self, request):
        """统计当日新增用户"""
        # 当日（过滤出用户创建时间大于等于今天的0时）
        # 1.获得"当日"的零时

        # 2.过滤用户数
        count = User.objects.filter(date_joined__gte=self.cur_0_time).count()
        return Response({
            "count": count,
            "date": self.cur_0_time
        })

    # 日活跃用户
    # GET
    # statistical/day_active/
    @action(methods=['get'], detail=False)
    def day_active(self, request):
        # 1.获得当日零时
        # 2.过滤统计用户数量
        count = User.objects.filter(last_login__gte=self.cur_0_time).count()
        # 3.构建响应数据
        return Response({
            "count": count,
            "date": self.cur_0_time.date()
        })

    # 日下单用户
    # GET
    # statistical/day_orders/
    @action(methods=['get'], detail=False)
    def day_orders(self, request):
        """统计日下单用户"""
        # 1.已知条件：当日零时
        # 2.目标数据：用户
        # 方案一：从从表入手，查询从表数据对象
        order_list = OrderInfo.objects.filter(create_time__gte=self.cur_0_time)
        # 2.从这些订单中找出用户
        user_list = []
        for order in order_list:
            user_list.append(order.user)
        # 3.user_list列表保存的是所有订单关联用户
        # 去重(因为只统计下单的用户数，所以重复下单的人要去掉)
        count = len(set(user_list))

        return Response({
            "count": count,
            "date": self.cur_0_time.date()
        })

        # 方案二：从主表入手

        # user_list = User.objects.filter(orderinfo__skus__create_time__gte=cur_0_time)
        # count = len(set(user_list))
        #
        # return Response({
        #     "count": count,
        #     "date": self.cur_0_time.date()
        # })

    # 月新增用户统计（30天）
    # GET
    # statistical/month_increment/
    @action(methods=['get'], detail=False)
    def month_increment(self, request):
        # 1.当日零时(终止时间)
        # 2.起始时间点
        start_0_time = self.cur_0_time - timedelta(days=29)

        # 3.起始时间点（零时）当日零时之间每一天新增的用户
        user_list = []
        for index in range(30):
            # 用于计算的某一天的0时
            calc_0_time = start_0_time + timedelta(days=index)
            next_0_time = calc_0_time + timedelta(days=1)
            count = User.objects.filter(date_joined__gte=calc_0_time, date_joined__lt=next_0_time).count()
            user_list.append({
                "count": count,
                "date": calc_0_time.date()
            })

        return Response(user_list)


# 日分类商品访问量
# statistical/goods_day_views/
class GoodsVisitCountView(ListAPIView):
    """序列化返回GoodsVisitCount多条数据"""
    permission_classes = [IsAdminUser]

    queryset = GoodsVisitCount.objects.all()
    serializer_class = GoodsVisitCountSerializer

    def get_queryset(self):
        cur_0_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE)). \
            replace(hour=0, minute=0, second=0, microsecond=0)

        return self.queryset.filter(create_time__gte=cur_0_time)
