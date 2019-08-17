from django.core.files.storage import Storage
from django.conf import settings

class FastDFSStorage(Storage):

    def _open(self, name, mode='rb'):
        """
        当要打开某个文件时就会调用此方法
        :param name: 要打开的文件名
        :param mode: 打开文件的模式
        """
        pass

    def _save(self, name, content):
        """
        当腰进行上传图片时就会自动调用此方法
        :param name: 要上传的文件名
        :param content: 要上传的文件二进制数据
        :return:file_id
        """
        pass

    def url(self, name):
        """当获取图片的绝对路径时就会调用此方法
        :param name:要访问的文件file_id
        :return:绝对路径 http://192.168.27.128:8888/ + name
        """
        return settings.FDFS_BASE_URL + name

