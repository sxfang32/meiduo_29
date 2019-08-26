from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings

def generate_openid_signature(wb_openid):
    """
    对openid进行加密
    :param openid: 要加密的openid数据
    :return: 加密后的openid
    """
    serializer = Serializer(settings.SECRET_KEY, 600)
    data = {'wb_openid': wb_openid}  # 把数据包装成字典
    openid_sign = serializer.dumps(data)  # 加密后返回的数据是bytes类型
    return openid_sign.decode()


def check_openid_sign(openid_sign):
    """
    对加密后的openid进行解密,回到原本样子
    :param openid_sign: 要解密的openid
    :return: 原本的openid
    """
    serializer = Serializer(settings.SECRET_KEY, 600)
    try:
        data = serializer.loads(openid_sign)
    except BadData:
        return None
    else:
        return data.get('wb_openid')
