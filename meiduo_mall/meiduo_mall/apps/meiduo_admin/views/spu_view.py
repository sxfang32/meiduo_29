from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from goods.models import SPU, GoodsCategory
from meiduo_admin.serializers.spu_serializer import *
from meiduo_admin.pages import MyPage


class SPUViewSet(ModelViewSet):
    queryset = SPU.objects.all().order_by('id')
    serializer_class = SPUModelSerializer
    pagination_class = MyPage

    def get_queryset(self):
        # 如果一个请求处理的视图是方法spu_brand
        # self.action指的就是处理当前请求的视图方法的名称
        if self.action == "spu_brands":
            # 那么返回的数据集是Brand的查询集
            return Brand.objects.all().order_by('id')
        return self.queryset.all()

    def get_serializer_class(self):
        # 如果一个请求处理的处理方法是spu_brands
        # 那么返回用于处理数据集的序列化器是
        if self.action == "spu_brands":
            return SPUBrandSimpleSerializer
        return self.serializer_class

    def spu_brands(self, request):
        """序列化返回所有品牌信息"""
        # 1.获得品牌数据对象的查询集
        brand_query = self.get_queryset()
        # 2.获得序列化器对象
        s = self.get_serializer(brand_query, many=True)
        # 3.序列化返回
        return Response(s.data)


class SPUCategoryView(ListAPIView):
    queryset = GoodsCategory.objects.all().order_by('id')
    serializer_class = SPUCategorySimpleSerializer

    def get_queryset(self):
        # 如果请求路径中有pk，需要根据这个pk过滤出二级或三级分类
        pk = self.kwargs.get('pk')
        if pk:
            return self.queryset.filter(parent_id=pk)
        return self.queryset.filter(parent=None)
