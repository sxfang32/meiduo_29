from rest_framework import serializers
from goods.models import Brand
from fdfs_client.client import Fdfs_client
from django.conf import settings
from meiduo_mall.utils.fastdfs.fdfs_storage import fdfs_send_filebuffer


class BrandModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            # 当前logo是一个文件类型的字段，在反序列化的时候
            # 会将前端传来的文件数据，反序列化组织成文件对象
            "logo",
            "first_letter"
        ]

    # def validate(self, attrs):
    #     file_obj = attrs.pop('logo')
    #     # 2.读取文件内容
    #     content = file_obj.read()
    #     # 3.使用fdfs客户端完成上传
    #     res = fdfs_send_filebuffer(content)
    #     # 4.新建客户图片数据
    #     if not res['Status'] == "Upload successed.":
    #         raise serializers.ValidationError('上传失败')
    #     attrs['logo'] = res['Remote file_id']
    #     return attrs

    # def create(self, validated_data):
    #     """
    #     问题：自带的create方法无法完成数据商城fdfs的操作
    #     :param validated_data:
    #     :return:
    #     """
    #     # 1.获得文件数据
    #     file_obj = validated_data.get('logo')
    #     content = file_obj.read()
    #     # 2.将该文件数据上传到fdfs
    #     res = fdfs_send_filebuffer(content)
    #     # 3.上传成功则，记录返回的文件ID
    #     if not res['Status'] == "Upload successed.":
    #         raise serializers.ValidationError('上传失败')
    #     # 4.构建模型类对象，保存数据库
    #     # 修改logo字段，以在MySQL中记录文件fdfs的id
    #     validated_data['logo'] = res['Remote file_id']
    #     return super().create(validated_data)
    #
    # def update(self, instance, validated_data):
    #     """
    #     更新文件的 上传操作
    #     :param instance:
    #     :param validated_data:
    #     :return:
    #     """
    #     # 1.获得文件数据
    #     file_obj = validated_data.get('logo')
    #     content = file_obj.read()
    #     # 2.将该文件数据上传到fdfs
    #     res = fdfs_send_filebuffer(content)
    #     # 3.上传成功则，记录返回的文件ID
    #     if not res['Status'] == "Upload successed.":
    #         raise serializers.ValidationError('上传失败')
    #     # 4.构建模型类对象，保存数据库
    #     # 修改logo字段，以在MySQL中记录文件fdfs的id
    #     validated_data['logo'] = res['Remote file_id']
    #     return super().update(instance,validated_data)
