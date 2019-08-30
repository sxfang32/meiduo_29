from goods.models import GoodsVisitCount
from rest_framework import serializers


# 定义序列化器
# 序列化GoodsVisitCOunt:category、count

class GoodsVisitCountSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GoodsVisitCount
        fields = ['category', 'count']
