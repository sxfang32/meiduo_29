from rest_framework import serializers
from goods.models import SpecificationOption


class OptModelSerializer(serializers.ModelSerializer):
    spec = serializers.StringRelatedField()
    spec_id = serializers.IntegerField()

    class Meta:
        model = SpecificationOption
        fields = [
            'id',
            'value',
            'spec',
            'spec_id'
        ]
