from django.contrib.auth import mixins
from django.views import View


class LoginRequiredView(mixins.LoginRequiredMixin, View):
    """判断登录视图基类"""
    pass