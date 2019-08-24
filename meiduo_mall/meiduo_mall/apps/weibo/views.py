
from django.shortcuts import render,redirect
from django import http
from django.contrib.auth import login
from django.conf import settings
from django.views import View

from users.models import User
from .utils import check_openid_sign,generate_openid_signature
from django_redis import get_redis_connection
from .models import OAuthWeiboUser
from .WeiboTool import OAuthWeibo

from meiduo_mall.utils.response_code import RETCODE
from carts.utils import merge_cart_cookie_to_redis
import re

import logging

loger = logging.getLogger('django')

class OauthSinaloginView(View):
    def get(self,request):

        # 提取前端用查询参数传入的next参数:记录用户从哪里去到login界面

        next = request.GET.get('next', '/')

        weibo = OAuthWeibo(client_id=settings.APP_KEY,client_key=settings.APP_KEY,
                            redirect_uri=settings.REDIRECT_URI,
                            state=next)
        # 拼接微博登陆连接
        login_url = weibo.get_weibo_url()

        return http.JsonResponse({'login_url': login_url, 'code': RETCODE.OK, 'errmsg': 'OK'})
class OauthSinaView(View):
    '''微博登陆过后的回调处理'''
    def get(self,request):

        code = request.GET.get('code')
        state = request.GET.get('state','/')


        wb = OAuthWeibo(client_id=settings.APP_KEY, client_key=settings.APP_KEY,
                           redirect_uri=settings.REDIRECT_URI,
                           )

        if not code:
            return http.JsonResponse({'code': RETCODE.SERVERERR, 'errors': '缺少code值'}, status=400)

        # 调用SDK中的get_access_token(code) 得到access_token
        access_token = wb.get_access_token(code)

        try:
            weibo_model = OAuthWeiboUser.objects.get(wb_openid=access_token)
        except OAuthWeiboUser.DoesNotExist:

            openid = generate_openid_signature(access_token)

            return render(request, 'sina_callback.html', {"access_token": openid})
        else:
            user = weibo_model.user
            login(request,user)
            response = redirect(state)
            response.set_cookie('username',user.username,max_age=settings.SESSION_COOKIE_AGE)

            # merge_cart_cookie_to_redis(request,user,response)
            return response

    def post(self, request):
        '''美多商城用户绑定到wb_openid'''
        # 接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code = request.POST.get('sms_code')
        openid = request.POST.get('wb_openid')

        if not all([mobile, password, sms_code, openid]):
            return http.HttpResponseForbidden('缺少必传参数')

        # 校验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号不存在')

        if not re.match(r'[a-zA-Z0-9]{8,20}', password):
            return http.HttpResponseForbidden('请输入8-20位密码')

        # 短信验证码校验暂时胜利

        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if sms_code_server is None or sms_code != sms_code_server.decode():
            return http.HttpResponseForbidden('短信验证码有误')

        # 校验openid
        access_token = check_openid_sign(openid)
        if access_token is None:
            # return http.HttpResponseForbidden('openid无效')
            return render(request, 'sina_callback.html', {'wb_openid_errmsg': '无效的access_token'})
        # 绑定用户
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 当前就要绑定一个新用户
            user = User.objects.create_user(
                username=mobile,
                password=password,
                mobile=mobile
            )
        else:
            # 如果用户存在，就检查用户密码
            if not user.check_password(password):
                return render(request, 'sina_callback.html', {'account_errmsg': '用户名或密码错误'})

            # 将用户绑定openid
            try:
                OAuthWeiboUser.objects.create(
                    wb_openid=access_token,
                    user=user
                )
            except:
                return render(request, 'sina_callback.html', {'wb_login_errmsg': '微博登录失败'})

            # 实现状态保持
            login(request, user)

            # 响应绑定结果
            next = request.GET.get('state')
            response = redirect(next)

            # 登陆是用户名写入到cookies，有效期为15天
            response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
            return response

