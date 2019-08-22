from django.shortcuts import render
from meiduo_mall.utils.views import LoginRequiredView

class PaymentURLView(LoginRequiredView):
    """拼接支付宝登录URL"""

    def get(self, request):
        pass
