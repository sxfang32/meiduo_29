from rest_framework.viewsets import ModelViewSet
from goods.models import SPUSpecification
from meiduo_admin.serializers.spec_serializer import *
from meiduo_admin.pages import MyPage


class SpecViewSet(ModelViewSet):
    queryset = SPUSpecification.objects.all().order_by('pk')
    serializer_class = SpecModelSerializer
    pagination_class = MyPage
