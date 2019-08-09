from django.shortcuts import render
from django.views import View
from django import http
import random
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection

from verifications.constants import *
from . import constants
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.libs.yuntongxun.sms import CCP

class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        # sdk生成图形验证码
        # name:唯一标识  text:图形验证码字符串   image_code:图片验证码bytes类型数据
        name, text, image_code = captcha.generate_captcha()
        # 连接redis
        redis_conn = get_redis_connection('verify_codes')
        # 将图形验证码字符串存储到redis数据库
        redis_conn.setex(uuid, constants.IMAGE_CODE_EXPIRE, text)
        # 响应
        return http.HttpResponse(image_code, content_type='image/jpg')


class SMSCodeView(View):
    """短信验证码"""

    def get(self, request, mobile):
        # 接收前端传入的数据
        query_dict = request.GET
        image_code_client = query_dict.get('image_code')
        uuid = query_dict.get('uuid')

        # 校验
        if all([image_code_client, uuid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 将redis中的图形验证码字符串获取出来.这是一个字节类型的数据
        image_code_server_bytes = redis_conn.get(uuid)
        # 图形验证码从redis获取出来之后就从Redis数据库中删除:让图形验证码只能用一次
        redis_conn.delete(uuid)
        # 判断redis中是否获取到图形验证码(判断是否过期)
        if image_code_server_bytes is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码错误'})
        # 从redis获取出来的数据注意数据类型问题byte，先进行decode操作
        image_code_server = image_code_server_bytes.decode()
        # 判断时要注意字典大小写问题
        if image_code_client.lower() != image_code_server.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码输入错误'})

        # 发送短信验证码
        # 生成随机数作为短信验证码
        sms_code = '%06d'% random.randint(0, 999999)
        # 将短信验证码存储到redis，key为了保持唯一，统一sms_手机号格式
        redis_conn.setex('sms_%s' % mobile, IMAGE_CODE_EXPIRE, sms_code)
        # 利用容联云平台发送短信
        # CCP().send_template_sms(手机号, [验证码, 过期时间：分钟], 使用的短信模板ID)
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
