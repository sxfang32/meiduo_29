from meiduo_admin.serializers.user_serializer import *
from rest_framework.generics import ListCreateAPIView
from users.models import User
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from meiduo_admin.pages import MyPage


class UserAPIView(ListCreateAPIView):
    queryset = User.objects.filter(is_staff=True).order_by('id')
    serializer_class = UserModelSerializer

    pagination_class = MyPage

    def get_queryset(self):
        """后续所有的序列化处理的数据集都是通过该函数获得
        只要重写该函数就可以控制处理的视图集"""

        # 请求对象：视图对象.request
        keyword = self.request.query_params.get('keyword')

        if keyword:
            return self.queryset.filter(username__contains=keyword)

        # .all()的目的是获得最新的数据，而不是从缓存中获取旧数据
        return self.queryset.all()
