from django.shortcuts import render, redirect
from django.conf import settings
from django.views import View
from django import http
from django.contrib.auth import login

from QQLoginTool.QQtool import OAuthQQ
from meiduo_mall.utils.response_code import RETCODE
from oauth.models import OAuthQQUser

import logging

logger = logging.getLogger('django')


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
        try:
            # 调用get_access_token
            access_token = auth_qq.get_access_token(code)
            # 调用get_openid
            openid = auth_qq.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.SERVERERR, 'errmsg': 'OAuth2.0认证失败'})

        try:
            # 去数据库中查询openID是否存在
            auth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果不存在，说明openID还没有绑定美多中的用户，应该去绑定
            context = {'openid': openid}
            return render(request, 'oauth_callback.html', context)

        else:
            # 如果存在，说明openID之前已经绑定过美多用户，那么直接代表登录成功
            user = auth_model.user
            # 状态保持
            login(request, user)
            # 向cookie存储username
            response = redirect(request.GET.get('state') or '/')
            response.set_cookie('username', user.username, max_age=settings.SSIONSE_COOKIE_AGE)
            # 重定向到指定的来源页
            return response
