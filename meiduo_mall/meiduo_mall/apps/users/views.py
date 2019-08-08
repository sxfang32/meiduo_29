from django.contrib.auth import login
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from .models import *
import re


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """展示用户注册芥界面"""
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
        if not all([username, password, password2, mobile, allow]):
            return HttpResponseForbidden('参数不全，请重新输入')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')
        if password2 != password:
            return HttpResponseForbidden('两次输入的密码不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('您输入的手机号格式不正确')

        # TODO:短信验证码校验后期补充

        # 使用表单提交，如果勾选了checkbox选项，会自动带上allow : on
        # if allow != 'on':
        #     return HttpResponseForbidden('请勾选用户协议')
        # 新增用户记录
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render, 'register.html', {"register_errmsg": "注册失败"}

        # 状态保持 JWT
        # 将用户的id值存储到session中，会生成一个session存储到对应用户自己的浏览器cookie中
        login(request, user)

        # 跳转到首页
        return redirect(reverse('contents:index'))


class UsernameCountView(View):
    """判断用户名是否重复"""

    def get(self, request, username):
        # 从数据库查询当前username是否重复
        count = User.objects.filter(username=username).count()
        # 响应
        return JsonResponse({"count": count})


class MobileCountView(View):
    """判断手机号是否重复"""
    def get(self, request, mobile):
        # 从数据库查询当前username是否重复
        count = User.objects.filter(mobile=mobile).count()
        # 响应
        return JsonResponse({"count": count})
