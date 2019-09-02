from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from goods.models import GoodsChannel, GoodsChannelGroup
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.channel_serializer import *


class ChannelViewSet(ModelViewSet):
    queryset = GoodsChannel.objects.all().order_by('id')
    serializer_class = ChannelSerializer
    pagination_class = MyPage


class ChannelGroupView(ListAPIView):
    queryset = GoodsChannelGroup.objects.all().order_by('pk')
    serializer_class = ChannelGroupSerializer
