import re

from django import http
from django.contrib.auth import login
from django.db import DatabaseError
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
from .utils import generate_openid_signature, check_openid_sign

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
        try:
            result = auth_weibo.request_access_token(code)
            uid = result.uid
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.SERVERERR, 'errmsg': 'OAuth2.0认证失败'})
        return render(request, 'sina_callback.html')


class ShowPageView(View):
    """展示绑定用户页面"""

    def get(self, request):

        auth_weibo = sinaweibopy3.APIClient(
            app_key=settings.APP_KEY,
            app_secret=settings.APP_SECRET,
            redirect_uri=settings.REDIRECT_URI)

        code = request.GET.get('code')
        result = auth_weibo.request_access_token(code)
        uid = result.uid
        # 查数据库看uid是否存在，不存在即绑定，存在即直接登录

        try:
            auth_model = OAuthWeiboUser.objects.get(wb_openid=uid)
        except OAuthWeiboUser.DoesNotExist:
            context = {'wb_openid': generate_openid_signature(uid)}
            return render(request, 'sina_callback.html', context)
        else:
            user = auth_model.user
            user_id = user.id
            username = user.username
            login(request, user)
            response = http.JsonResponse(
            {'code': RETCODE.OK, 'errmsg': 'OK', 'user_id': user_id, 'username': username, 'access_token': uid})

            return response

    def post(self, request):
        """uid绑定用户逻辑"""

        query_dict = request.POST
        mobile = query_dict.get('mobile')
        password = query_dict.get('password')
        sms_code = query_dict.get('sms_code')
        openid_sign = query_dict.get('uid')
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

        # 对uid进行解密
        uid = check_openid_sign(openid_sign)

        if uid is None:
            return http.HttpResponseForbidden('uid无效')
        try:
            user = User.objects.get(mobile=mobile)
            if user.check_password(password) is False:
                return http.HttpResponseForbidden('绑定的用户信息填写不正确')
        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)

        try:
            OAuthWeiboUser.objects.create(user=user, wb_openid=uid)
        except DatabaseError:
            return render(request, 'sina_callback.html', {'weibo_login_error': '微博登录失败'})

        login(request, user)

        response = redirect('/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

        # 合并购物车
        merge_cart_cookie_to_redis(request, response)
        return response

# from django.shortcuts import render, redirect
# from django.views import View
# from QQLoginTool.QQtool import OAuthQQ
# from django.contrib.auth import settings, login
# from django.http import JsonResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponse
# from meiduo_mall.utils.response_code import RETCODE
# from users.models import User
# from django_redis import get_redis_connection
#
# import re
# import json
#
# import logging
# from carts.utils import merge_cart_cookie_to_redis
# from .models import OAuthWeiboUser
# from .sinaweibopy3 import APIClient
#
# # from .utils import OAuth_WEIBO
#
#
# """构建微博登录跳转链接"""
#
#
# class WeiBoOAuthUserView(View):
#     def get(self, request):
#         # 1、创建微博对象
#         sina = APIClient(app_key=settings.APP_KEY, app_secret=settings.APP_SECRET,
#                          redirect_uri=settings.REDIRECT_URI, )
#         # 4、构建跳转连接
#         login_url = sina.get_authorize_url()
#
#         # 5、返回跳转连接
#         return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})
#
#
# class UnKnwoCode(View):
#     def get(self, request):
#         code = request.GET.get('code')
#         if not code:
#             return HttpResponse({'errors': '缺少code值'}, status=400)
#         access_token = request.COOKIES.get('access_token_s')
#         try:
#             sina_user = OAuthWeiboUser.objects.get(wb_openid=access_token)
#         except OAuthWeiboUser.DoesNotExist:
#             return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'access_token': access_token})
#         user = sina_user.user
#         user_id = user.id
#         username = user.username
#         return JsonResponse(
#             {'code': RETCODE.OK, 'errmsg': 'OK', 'user_id': user_id, 'username': username, 'access_token': access_token})
#
#     # 用户点击保存：post请求，在当前类视图中添加post方法
#     def post(self, request):
#         # 接收数据
#         json_dict = json.loads(request.body.decode())
#         password = json_dict.get('password')
#         mobile = json_dict.get('mobile')
#
#         # 图形验证码在发送短信前已经验证了，这里不再验证
#
#         sms_code = json_dict.get('sms_code')
#
#         access_token = request.COOKIES.get('access_token_s')
#
#         # 检查接收数据是否齐全
#         if all([mobile, password, sms_code, access_token]) is False:
#             return HttpResponseForbidden('缺少必传参数')
#         # 判断手机号是否合法
#         if not re.match(r'^1[3-9]\d{9}$', mobile):
#             return HttpResponseForbidden('请输入正确的手机号码')
#         # 判断密码是否合格
#         if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
#             return HttpResponseForbidden('请输入8-20位的密码')
#
#         # 建立数据库链接，判断短信验证码是否正确
#         redis_connet = get_redis_connection('verify_code')
#         sms_code_server = redis_connet.get('sms_%s' % mobile)
#         if not sms_code_server or sms_code != sms_code_server.decode():
#             return JsonResponse({'code': '400', 'message': '短信验证失败'})
#
#         # print(date_openid)
#         if not access_token:
#             return HttpResponseForbidden('无效的access_token')
#
#         # 保存注册用户,如果用户不存在
#         try:
#             user = User.objects.get(mobile=mobile)
#         except User.DoesNotExcist:
#             # 新建用户
#             user = User.objects.create(username=mobile, password=password, mobile=mobile)
#
#         # 用户存在，检查密码
#         else:
#             if not user.check_password(password):
#                 return render(request, 'sina_callback.html', {'error_phone_message': '用户名或密码错误'})
#
#         # 将用户绑定access_token
#         try:
#             # 第一个user为外键,第二个user为主表的数据对象,
#             OAuthWeiboUser.objects.create(user=user, wb_openid=access_token)
#         except OAuthWeiboUser.DoesNotExist:
#             return render(request, 'sina_callback.html', {'error_sms_code_message': '微博登录失败'})
#
#         user_id = user.id
#         username = user.username
#         response = JsonResponse(
#             {'code': RETCODE.OK, 'errmsg': 'OK', 'user_id': user_id, 'username': username, 'token': access_token})
#         """登录即合并购物车"""
#         merge_cart_cookie_to_redis(request, user, response)
#         return response
#
#
# """获取access_token"""
#
#
# class GetWeiBoCode(View):
#     def get(self, request):
#         # 1、获取code值
#         code = request.GET.get('code', None)
#
#         # 2、判断code是否传递过来
#         if not code:
#             return HttpResponse({'errors': '缺少code值'}, status=400)
#
#         # 3、通过code值获取access_token值
#         # 创建sina对象
#         sina = APIClient(app_key=settings.APP_KEY, app_secret=settings.APP_SECRET,
#                          redirect_uri=settings.REDIRECT_URI, )
#         try:
#             access_token_dict = sina.request_access_token(code)
#             access_token = access_token_dict.get('access_token')
#         except:
#             access_token = request.COOKIES.get('access_token_s')
#         # 5、判断access_token是否绑定过用户
#         try:
#             sina_user = OAuthWeiboUser.objects.get(wb_openid=access_token)
#
#         except OAuthWeiboUser.DoesNotExist:
#             response = render(request, 'sina_callback.html')
#             response.set_cookie('access_token_s', access_token)
#             return response
#         else:
#             # access_token已绑定用户处理
#             # 获取sina_user对象的外键(user)(也就是user表的id)
#             user = sina_user.user
#             # 状态保持
#             login(request, user)
#             # 获取state值(从哪个页面登录，登录后回到哪个页面)
#             state = request.GET.get('state', '/')
#             # 重定向到state值的页面
#             response = redirect(state)
#
#             # 设置cookie值,展示登录信息
#             response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
#
#             """登录即合并购物车"""
#             merge_cart_cookie_to_redis(request, user, response)
#
#             # 返回响应
#         return response
