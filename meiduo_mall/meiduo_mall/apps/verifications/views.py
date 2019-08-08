from django.shortcuts import render
from django.views import View
from django import http
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from . import constants


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
