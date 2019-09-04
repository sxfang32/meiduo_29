from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client
from rest_framework import serializers


def fdfs_send_filebuffer(file_buffer):
    """
    上传文件数据到fdfs
    :param file_buffer: 文件数据——>字节数据
    :return:
    """
    # 1.构建fdfs连接对象
    conn = Fdfs_client(settings.FDFS_CONF_PATH)
    # 2.调用上传函数
    res = conn.upload_by_buffer(file_buffer)
    # 3.返回结果
    return res


class FastDFSStorage(Storage):
    """自定义存储后端"""

    def _open(self, name, mode='rb'):
        """
        当要打开某个文件时就会调用此方法
        :param name: 要打开的文件名
        :param mode: 打开文件的权限
        ：:return: 本地打开的文件对象
        """
        # 咱们的后台管理业务，不需要将前端传来的图片文件保存在本地
        return None

    def _save(self, name, content, max_length=None):
        """
        当要进行上传图片时就会自动调用此方法
        保存前端传来的文件（上传fdfs文件）
        # :param name: 要上传的文件名
        :param content: 要上传的文件对象 --> 序列化器校验之后得到的文件对象
        :param max_length:最大长度
        :return:file_id 返回文件的标识，保存到MySQL
        """
        res = fdfs_send_filebuffer(content.read())
        if res['Status'] != "Upload successed.":
            raise serializers.ValidationError('上传失败')
        return res["Remote file_id"]

    def url(self, name):
        """当获取图片的绝对路径时就会调用此方法
        序列化返回的当前文件字段结果
        :param name:要访问的文件file_id
        :return:绝对路径 http://192.168.27.128:8888/ + name
        """
        return settings.FDFS_BASE_URL + name

    def exists(self, name):
        """
        django存储后端使用该函数判断保存的文件是否存在
        :param name: 文件名称
        :return: 布尔值
        """

        # return True # 保存的文件存在
        return False # 保存的文件不存在

