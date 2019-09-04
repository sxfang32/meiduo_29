from rest_framework.viewsets import ModelViewSet
from goods.models import Brand
from meiduo_admin.serializers.brands_serializer import *
from meiduo_admin.pages import MyPage


class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all().order_by('id')
    serializer_class = BrandModelSerializer
    pagination_class = MyPage


