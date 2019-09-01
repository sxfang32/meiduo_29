from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from goods.models import SKU, GoodsCategory, SPU, SPUSpecification
from meiduo_admin.serializers.sku_serializer import *
from meiduo_admin.pages import MyPage


class SKUViewSet(ModelViewSet):
    queryset = SKU.objects.all().order_by('id')
    serializer_class = SKUModelSerializer
    pagination_class = MyPage

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()


class GoodsCategoryView(ListAPIView):
    queryset = GoodsCategory.objects.filter(parent_id__gt=37).order_by('id')
    serializer_class = GoodsCategorySimpleSerializer


class SPUSimpleView(ListAPIView):
    # queryset = SPU.objects.filter(category3_id=)
    queryset = SPU.objects.all()
    serializer_class = SPUSimpleerializer


class SPUSpecOptView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecSerializer

    def get_queryset(self):
        # 1.提取前端传来的spu_id
        spu_id = self.kwargs.get('pk')
        # 2.过滤出spu_id关联的所有的SPUSpecification对象
        # 3.返回过滤后数据集
        return self.queryset.filter(spu_id=spu_id)