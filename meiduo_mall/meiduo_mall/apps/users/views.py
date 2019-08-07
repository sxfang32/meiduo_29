from django.shortcuts import render
from django.views import View


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """展示用户注册芥界面"""
        return render(request, 'register.html')

    def post(self, request):
        """用户注册逻辑"""
        # 接收请求体中的表单数据

        # 校验数据

        # 新增用户记录

        # 跳转到首页
        pass
