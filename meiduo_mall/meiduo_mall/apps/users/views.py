import json

from django.contrib.auth import login, authenticate, logout, mixins
from django.core.mail import send_mail
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.views import View
from django import http
from django.conf import settings
import re
from django_redis import get_redis_connection

from meiduo_mall.utils.response_code import RETCODE
from .models import *
from meiduo_mall.utils.views import LoginRequiredView
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_email_verify_url

class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """展示用户注册界面"""
        return render(request, 'register.html')

    def post(self, request):
        """用户注册逻辑"""
        # 接收请求体中的表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        sms_code = query_dict.get('sms_code')
        allow = query_dict.get('allow')
        # 校验数据
        if all([username, password, password2, mobile, allow]) is False:
            return http.HttpResponseForbidden('参数不全，请重新输入')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password2 != password:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')

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

        # 使用表单提交，如果勾选了checkbox选项，会自动带上allow : on
        # if allow != 'on':
        #     return HttpResponseForbidden('请勾选用户协议')
        # 新增用户记录
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})

        # 状态保持 JWT
        # 将用户的id值存储到session中，会生成一个session存储到对应用户自己的浏览器cookie中
        login(request, user)

        # 跳转到首页
        response = redirect('/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        return response


class UsernameCountView(View):
    """判断用户名是否重复"""

    def get(self, request, username):
        # 从数据库查询当前username是否重复
        count = User.objects.filter(username=username).count()
        # 响应
        return http.JsonResponse({"count": count})


class MobileCountView(View):
    """判断手机号是否重复"""

    def get(self, request, mobile):
        # 从数据库查询当前username是否重复
        count = User.objects.filter(mobile=mobile).count()
        # 响应
        return http.JsonResponse({"count": count})


class LoginView(View):
    """用户登录"""

    def get(self, request):
        """提供登录的界面"""
        return render(request, 'login.html')

    def post(self, request):
        """登录功能逻辑"""
        # 1.接收请求体表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        # 2.校验
        user = authenticate(request, username=username, password=password)
        # 如果登录失败
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 3.状态保持
        login(request, user)

        # 如果用户没有勾选记住登录
        # 如果session过期时间设置为None，表示使用默认的14天，如果设置为0，代表关闭浏览器失效
        # 如果cookie过期时间设置为None，表示关闭浏览器就过期，如果设置为0，代表直接删除
        if remembered is None:
            request.session.set_expiry(0)  # 是指session的过期时间为关闭浏览器过期
        # 4.重定向

        next = request.GET.get('next')  # 尝试去获取查询参数中是否有用户界面的来源，如果有来源，成功登录后跳转到来源界面
        response = redirect(next or '/')  # 创建响应对象
        # 给cookie设置username
        response.set_cookie('username', user.username,
                            max_age=None if remembered is None else settings.SESSION_COOKIE_AGE)
        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        # 1.清除状态保持
        logout(request)

        # 2.清除cookie中的username
        response = redirect('/login/')
        response.delete_cookie('username')  # 其实delete_cookie本质就是set_cookie(max_age=0)

        # 3.重定向到login界面
        return response


# class InfoView(View):
#     """用户中心"""
#     def get(self, request):
#         # 如果当前是登录用户，直接响应用户中心页面
#         if request.user.is_authenticated:
#             return render(request, 'user_center_info.html')
#         else:
#             return redirect('/login/?next=/info/')

class InfoView(mixins.LoginRequiredMixin, View):
    """用户中心页面展示"""

    def get(self, request):
        """提供个人信息界面"""
        content = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', content)


class EmailView(LoginRequiredView):
    """添加邮箱功能"""

    def put(self, request):
        """添加邮箱（本质是把空值改掉）"""
        # 接收请求体中的数据
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验数据
        if not email:
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # return http.JsonResponse({'code': RETCODE.EMAILERR, 'errmsg': '邮箱格式错误'})
            return http.HttpResponseForbidden('邮箱格式不正确')
        # 业务逻辑实现
        # 获取当前登录用户user
        user = request.user

        # 修改email
        User.objects.filter(username=user.username, email='').update(email=email)

        # 发送邮件
        # send_mail(subject='美多商城', # 邮件主题
        #           message='邮件普通内容', # 邮件普通内容
        #           from_email='美多商城<itcast99@163.com>', # 发件人
        #           recipient_list=[email],
        #           html_message="<a href='http://www.itcast.cn''>传智<a>")
        # verify_url = 'http://www.meiduo.site:8000/verify_email?token='
        verify_url = generate_email_verify_url(request.user)
        send_verify_email.delay(email, verify_url)
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg':'添加邮箱成功'})
