from rest_framework.viewsets import ModelViewSet
from goods.models import SPU
from meiduo_admin.serializers.spu_serializer import *
from meiduo_admin.pages import MyPage


class SPUViewSet(ModelViewSet):
    queryset = SPU.objects.all().order_by('id')
    serializer_class = SPUModelSerializer
    pagination_class = MyPage
