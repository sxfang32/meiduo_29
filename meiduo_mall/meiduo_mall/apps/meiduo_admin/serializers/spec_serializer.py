from rest_framework import serializers
from goods.models import SPUSpecification


class SpecModelSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    class Meta:
        model = SPUSpecification
        fields = ['id', 'name', 'spu', 'spu_id']
