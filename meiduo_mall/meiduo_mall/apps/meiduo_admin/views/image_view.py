from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from goods.models import SKU,SKUImage
from meiduo_admin.serializers.image_serializer import *
from meiduo_admin.pages import MyPage


class ImageViewSet(ModelViewSet):
    queryset = SKUImage.objects.all().order_by('id')
    serializer_class = ImageModelSerializer
    pagination_class = MyPage

    def get_skus(self, request):
        """使用SKUSimpleSerializer，序列化返回多条数据"""
        # 1.获得多条数据
        skus_query = SKU.objects.all()
        # 2.获得序列化器对象
        s = SKUSimpleSerializer(skus_query, many=True)
        # 3.序列化返回
        return Response(s.data)
