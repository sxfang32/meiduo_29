from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.conf import settings
from django.views import View
from django import http
from django.contrib.auth import login
import re
from django_redis import get_redis_connection

from QQLoginTool.QQtool import OAuthQQ
from meiduo_mall.utils.response_code import RETCODE
from oauth.models import OAuthQQUser
from .utils import generate_openid_signature, check_openid_signature
from users.models import User
import logging
from carts.utils import merge_cart_cookie_to_redis

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
            context = {'openid': generate_openid_signature(openid)}
            return render(request, 'oauth_callback.html', context)

        else:
            # 如果存在，说明openID之前已经绑定过美多用户，那么直接代表登录成功
            user = auth_model.user
            # 状态保持
            login(request, user)
            # 向cookie存储username
            response = redirect(request.GET.get('state') or '/')
            response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
            # 重定向到指定的来源页
            return response

    def post(self, request):
        """openID绑定用户逻辑"""
        # 接收表单数据
        query_dict = request.POST
        mobile = query_dict.get('mobile')
        password = query_dict.get('password')
        sms_code = query_dict.get('sms_code')
        openid_sign = query_dict.get('openid')
        # 校验数据
        if all([mobile, password, sms_code, openid_sign]) is False:
            return http.HttpResponseForbidden('参数不全，请重新输入')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号码格式不正确')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        # 短信验证码校验
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 将redis中的短信验证码字符串获取出来
        sms_code_server_bytes = redis_conn.get('sms_%s' % mobile)
        # 短信验证码从redis获取出来之后就从Redis数据库中删除:让图形验证码只能用一次
        redis_conn.delete('sms_%s' % mobile)
        # 判断redis中是否获取到短信验证码(判断是否过期)
        if sms_code_server_bytes is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '短信验证码错误'})
        # 从redis获取出来的数据注意数据类型问题byte
        sms_code_server = sms_code_server_bytes.decode()
        # 判断短信验证码是否相等
        if sms_code != sms_code_server:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '短信验证码输入错误'})

        # 对openID进行解密
        openid = check_openid_signature(openid_sign)
        if openid is None:
            return http.HttpResponseForbidden('openid无效')
        try:
            # 以mobile字段进行查询user表
            # 如果查到了，说明此手机号在美多商城之前已经注册，老用户
            user = User.objects.get(mobile=mobile)
            if user.check_password(password) is False:
                return http.HttpResponseForbidden('绑定的用户信息填写不正确')
        except User.DoesNotExist:
            # 如果没有查询到，说明此手机号时新的，创建一个新的user
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)

        # 新增oauth_qq表的一个记录
        try:
            OAuthQQUser.objects.create(user=user, openid=openid)
        except DatabaseError:
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})
        # 绑定完成即代表登录成功
        # 状态保持
        login(request, user)

        # 将username保存到cookie中
        response = redirect(request.GET.get('state') or '/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

        # 合并购物车
        merge_cart_cookie_to_redis(request, response)
        return response
