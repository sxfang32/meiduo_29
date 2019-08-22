from django.shortcuts import render
from alipay import AliPay
from django import http
import os
from django.conf import settings

from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredView
from orders.models import OrderInfo


class PaymentURLView(LoginRequiredView):
    """拼接支付宝登录URL"""

    def get(self, request, order_id):

        # 1.校验
        try:
            order = OrderInfo.objects.get(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                                          user=request.user)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')


        # 2.创建AliPay对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 3.调用alipay的api_alipay_trade_page_pay方法得到支付宝登录url后面的查询参数
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,   # 美多的订单编号
            total_amount=str(order.total_amount),   # 注意将Decimal转成字符串
            subject='美多商城：%s' % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 4.拼接支付宝登录url
        # 电脑网站支付真实url，需要跳转到'https://openapi.alipay.com/gateway.do'
        # 电脑网站支付开发环境，需要跳转到'https://openapi.alipaydev.com/gateway.do'
        alipay_url = settings.ALIPAY_URL + '?' + order_string

        # 5.响应
        return http.JsonResponse({'code':RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})


class PaymentStatusView(LoginRequiredView):
    """保存订单信息"""
    def get(self, request):
        return render(request, 'pay_success.html')
