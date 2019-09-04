from rest_framework import serializers
from goods.models import SKUImage, SKU
from meiduo_mall.utils.fastdfs.fdfs_storage import fdfs_send_filebuffer


class ImageModelSerializer(serializers.ModelSerializer):
    # 可以用作序列化:关联主表对象的ID
    # 也可以用作反序列化：反序列化传入的值也是管理主表的ID
    # 注意事项：如果PrimaryKeyRelatedField作用于反序列化，那么必须通过queryset约束条件
    #             指明管理的主表的对象查询集合
    # 反序列化行为：需要给他一个主表对象的id，接着会根据这个id，在queryset的约束条件中过滤出主表关联对象
    # sku = serializers.PrimaryKeyRelatedField

    class Meta:
        model = SKUImage
        fields = [
            'id',
            'sku',
            'image'
        ]

    # def validate_image(self, value):
    #     """
    #
    #     :param value: 经过前序校验的当前字段的值，是一个文件对象
    #     :return:
    #     """
    #     pass
    # # TODO 对单一字段进行校验

    # def validate(self, attrs):
    #     file_obj = attrs.pop('image')
    #     # 2.读取文件内容
    #     content = file_obj.read()
    #     # 3.使用fdfs客户端完成上传
    #     res = fdfs_send_filebuffer(content)
    #     # 4.新建客户图片数据
    #     if not res['Status'] == "Upload successed.":
    #         raise serializers.ValidationError('上传失败')
    #     attrs['image'] = res['Remote file_id']
    #     return attrs

    # def create(self, validated_data):
    #     # 上传fdfs文件
    #
    #     # 1。获得文件对象
    #     file_obj = validated_data.pop('image')
    #     # 2.读取文件内容
    #     content = file_obj.read()
    #     # 3.使用fdfs客户端完成上传
    #     res = fdfs_send_filebuffer(content)
    #     # 4.新建客户图片数据
    #     if not res['Status'] == "Upload successed.":
    #         raise serializers.ValidationError('上传失败')
    #     validated_data['image'] = res['Remote file_id']
    #     return super().create(validated_data)
    #
    # def update(self, instance, validated_data):
    #     # 1。获得文件对象
    #     file_obj = validated_data.pop('image')
    #     # 2.读取文件内容
    #     content = file_obj.read()
    #     # 3.使用fdfs客户端完成上传
    #     res = fdfs_send_filebuffer(content)
    #     # 4.新建客户图片数据
    #     if not res['Status'] == "Upload successed.":
    #         raise serializers.ValidationError('上传失败')
    #     validated_data['image'] = res['Remote file_id']
    #     return super().update(instance, validated_data)


class SKUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ['id', 'name']
