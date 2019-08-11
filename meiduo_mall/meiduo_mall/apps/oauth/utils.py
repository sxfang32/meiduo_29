from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadData
from django.conf import settings


def generate_openid_signature(openid):
    """对openid进行加密，返回加密后的openID"""
    # 1.创建加密的实例对象
    serializer = Serializer(settings.SECRET_KEY, 600)
    # 2.调用dumps方法进行加密，返回bytes类型
    data = {'openid':openid}
    openid_sign = serializer.dumps(data)
    # 3.返回
    return openid_sign.decode()


def check_openid_signature(openid_sign):
    """对openID进行解密"""
    # 1.创建加密/解密实例
    serializer = Serializer(settings.SECRET_KEY, 600)
    try:
        # 调用loads方法进行解密
        data = serializer.loads(openid_sign)
    except BadData:
        return None
    # 返回
    return data.get('openid')