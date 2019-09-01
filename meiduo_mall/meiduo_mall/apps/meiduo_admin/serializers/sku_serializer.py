from rest_framework import serializers
from goods.models import SKU, SKUSpecification, GoodsCategory, SPU, SpecificationOption, SPUSpecification


class SKUSpecModelSerializer(serializers.ModelSerializer):
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()

    class Meta:
        model = SKUSpecification
        fields = ['spec_id', 'option_id']


class SKUModelSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    category = serializers.StringRelatedField()
    category_id = serializers.IntegerField()

    specs = SKUSpecModelSerializer(many=True)

    class Meta:
        model = SKU
        fields = "__all__"

    def create(self, validated_data):
        """ModelSerializer暂时无法完成中间表数据的构建，需要重写"""
        # 1.在有效数据中提取记录的中间表数据
        specs = validated_data.pop('specs')
        # 2.sku主表对象新建
        # instance = self.Meta.model.objects.create(**validated_data)
        instance = super().create(validated_data)
        # 3.创建中间表数据
        for spec in specs:
            spec['sku_id'] = instance.id
            SKUSpecification.objects.create(**spec)
        return instance

    def update(self, instance, validated_data):
        # 更新sku数据的同事，需要更新中间表数据
        # 中间表数据不一定只更新选项，有可能规格都变

        # 1.提取中间表数据
        specs = validated_data.pop('specs')
        # 2.更新SKU主表数据
        instance = super().update(instance, validated_data)
        # 3.更新中间表数据（1.删除原有表数据，2根据根据更新接口传来的spec中心创建数据）
        SKUSpecification.objects.filter(sku_id=instance.id).delete()
        for spec in specs:
            spec['sku_id'] = instance.id
            SKUSpecification.objects.create(**spec)
        return instance



class GoodsCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = ['id', 'name']


class SPUSimpleerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ['id', 'name']


class SPUSpecOptionsSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = ['id', 'value']


class SPUSpecSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    # 与当前规格对象关联的所有选项表对象
    options = SPUSpecOptionsSimpleSerializer(many=True)

    class Meta:
        model = SPUSpecification
        fields = [
            'id',
            'name',
            'spu',
            'spu_id',
            'options'
        ]
