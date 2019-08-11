import logging

from django.shortcuts import render
from django.conf import settings
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django import http

from meiduo_mall.utils.response_code import RETCODE


class QQAuthURLView(View):
    """拼接QQ登录"""

    def get(self, request):
        # 获取查询参数中的界面来源
        next = request.GET.get('next', '/')

        # 创建QQ登录工具对象
        # auth_qq = OAuthQQ(client_id='app_id', client_secret='app_key',redirect_uri='登录成功后的回调地址',state='将来会原样带回')
        auth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI,
                          state=next)

        # 调用它的get_qq_url方法，得到拼接好的QQ登录url
        login_url = auth_qq.get_qq_url()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class QQAuthUserView(View):
    """QQ登录成功后的回调处理"""
    def get(self, request):

        # 获取查询参数中的code
        code = request.GET.get('code')
        # 校验
        if code is None:
            return http.HttpResponseForbidden('缺少code')
        # 创建QQ登录工具对象
        auth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI)
        # 调用get_access_token
        access_token = auth_qq.get_access_token(code)
        # 调用get_openid
        openid = auth_qq.get_open_id(code)

        pass
