from django.contrib.auth import login
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.http import HttpResponseForbidden, HttpResponse
from users.models import *
import re


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """展示用户注册芥界面"""
        return render(request, 'register.html')

    def post(self, request):
        """用户注册逻辑"""
        # 接收请求体中的表单数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
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
        # 使用表单提交，如果勾选了checkbox选项，会自动带上allow : on
        if allow != 'on':
            return HttpResponseForbidden('请勾选用户协议')
        # 新增用户记录
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render, 'register.html', {"register_errmsg": "注册失败"}

        login(request, user)

        # 跳转到首页
        return redirect(reverse('contents:index'))

