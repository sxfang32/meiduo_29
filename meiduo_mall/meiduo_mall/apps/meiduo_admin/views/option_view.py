from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from goods.models import SpecificationOption, SPUSpecification
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.option_serializer import *
from meiduo_admin.serializers.spec_serializer import SpecModelSerializer


class OptViewSet(ModelViewSet):
    queryset = SpecificationOption.objects.all().order_by('id')
    serializer_class = OptModelSerializer
    pagination_class = MyPage


class OptSpecView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecModelSerializer
