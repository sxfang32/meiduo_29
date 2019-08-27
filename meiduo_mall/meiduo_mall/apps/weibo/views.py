import json
import random
import re

from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
import logging

from django_redis import get_redis_connection

from carts.utils import merge_cart_cookie_to_redis
from meiduo_mall.utils.response_code import RETCODE
from users.models import User
from . import sinaweibopy3
from .models import OAuthWeiboUser

logger = logging.getLogger('django')


class WeiboAuthURLView(View):
    """拼接微博登录URL"""

    def get(self, request):
        # 获取查询参数中的界面来源
        next = request.GET.get('next', '/')

        # 创建微博登录工具对象
        auth_weibo = sinaweibopy3.APIClient(
            app_key=settings.APP_KEY,
            app_secret=settings.APP_SECRET,
            redirect_uri=settings.REDIRECT_URI)

        # 调用get_authorize_url方法，得到拼接好的微博登录url
        login_url = auth_weibo.get_authorize_url()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class WeiboAuthUserView(View):
    """微博登录成功后的回调处理"""

    def get(self, request):
        # 获取查询参数中的code
        code = request.GET.get('code')

        # 校验
        if code is None:
            return http.HttpResponseForbidden('缺少code')
        auth_weibo = sinaweibopy3.APIClient(
            app_key=settings.APP_KEY,
            app_secret=settings.APP_SECRET,
            redirect_uri=settings.REDIRECT_URI)

        # 获取access_token和uid
        result = auth_weibo.request_access_token(code)
        access_token = result.access_token
        uid = result.uid

        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex(code, 3600, access_token)
        return render(request, 'sina_callback.html')


class ShowPageView(View):
    """展示绑定用户页面"""

    def get(self, request):

        code = request.GET.get('code')

        redis_conn = get_redis_connection('verify_codes')
        access_token_bytes = redis_conn.get(code)
        redis_conn.delete(code)
        if not access_token_bytes:
            return http.JsonResponse({"message": "非法请求或code已过期"}, status=400)
        access_token = access_token_bytes.decode()

        # 判断用户是否登录过
        try:
            user = OAuthWeiboUser.objects.get(wb_openid=access_token)
            login(request, user)
            data = {
                "user_id": user.id,
                "username": user.username,
                "token": access_token
            }
            response = http.JsonResponse(data=data)
            response.set_cookie("username", user.username, max_age=settings.SESSION_COOKIE_AGE)
            return response
        except OAuthWeiboUser.DoesNotExist:
            return http.JsonResponse({"access_token": access_token})

    def post(self, request):
        """uid绑定用户逻辑"""

        query_dict = json.loads(request.body.decode())
        mobile = query_dict.get('mobile')
        password = query_dict.get('password')
        sms_code = query_dict.get('sms_code')
        access_token = query_dict.get('access_token')
        # 校验数据
        if all([mobile, password, sms_code, access_token]) is False:
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

        try:
            user = User.objects.get(mobile=mobile)
            password_sy = user.check_password(password)
            if not password_sy:
                return http.JsonResponse({"message": "密码错误"}, status=406)
            OAuthWeiboUser.objects.get(user=user)
            return http.JsonResponse({"message": "手机号以备绑定"}, status=407)
        except OAuthWeiboUser.DoesNotExist:
            wb_user = OAuthWeiboUser(
                user_id=user.id,
                wb_openid=access_token
            )
            wb_user.save()
            user_m = wb_user.user
        except User.DoesNotExist:
            user_m = User(
                mobile=mobile,
                username="sms_%s" % mobile,
                password=password
            )
            user_m.save()
        login(request, user_m)
        response = http.JsonResponse({"token": access_token, "user_id": user_m.id, "username": user_m.username})
        response.set_cookie("username", user_m.username, max_age=settings.SESSION_COOKIE_AGE)
        return response

