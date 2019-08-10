from django.contrib.auth.backends import ModelBackend
import re

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