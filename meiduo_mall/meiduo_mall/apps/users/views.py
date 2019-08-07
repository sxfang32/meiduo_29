from django.shortcuts import render
from django.views import View


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """展示用户注册芥界面"""
        return render(request, 'register.html')
