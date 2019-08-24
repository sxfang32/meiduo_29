from django.contrib.auth.backends import ModelBackend
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings
from .models import User


def get_user_by_account(account):
    """
    通过传入用户名或手机号动态查询user
    :param account: username 或 mobile
    :return: user or None
    """
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义登录认证后端类"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1.查询user（可以通过用户名或手机号动态查询用户）
        user = get_user_by_account(username)
        # 2.校验密码是否正确
        if user and user.check_password(password):
            # 3.返回user或None
            return user


def generate_email_verify_url(user):
    """拿到用户信息进行加密并拼接激活url"""
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)

    data = {'user_id': user.id, 'email': user.email}

    token = serializer.dumps(data).decode()

    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token

    return verify_url


def check_email_verify_url(token):
    """
    对token进行解密，然后查询到用户
    :param token: 要解密的用户数据
    :return: user or None
    """
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    try:
        # 如果解密失败抛BadData异常
        data = serializer.loads(token)
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            # 如果查不到信息抛DoesNotExist异常
            user = User.objects.get(id=user_id, email=email)
            return user
        except User.DoesNotExist:
            return None
    except BadData:
        return None


def generate_access_token(user):
    """对access_token加密"""
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    data = {'user_id': user.id}
    access_token = serializer.dumps(data).decode()
    return access_token


def check_access_token(access_token):
    """对access_token解密"""
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    try:
        # 如果解密失败抛BadData异常
        data = serializer.loads(access_token)
        user_id = data.get('user_id')
        try:
            # 如果查不到信息抛DoesNotExist异常
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            return None
    except BadData:
        return None
