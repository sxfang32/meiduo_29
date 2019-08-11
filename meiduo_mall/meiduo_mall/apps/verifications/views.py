from django.shortcuts import render
from django.views import View
from django import http
import random
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection

from verifications.constants import *
from . import constants
from meiduo_mall.utils.response_code import RETCODE
from celery_tasks.sms.tasks import send_sms_code

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
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 发短信之前先尝试的去redis获取发送过的标记
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 判断是否有发送过的标记
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '频繁发送短信'})
        # 接收前端传入的数据
        query_dict = request.GET
        image_code_client = query_dict.get('image_code')
        uuid = query_dict.get('uuid')

        # 校验
        if all([image_code_client, uuid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

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
        sms_code = '%06d' % random.randint(0, 999999)
        # 创建Redis管道
        pl = redis_conn.pipeline()
        # 将短信验证码存储到redis，key为了保持唯一，统一sms_手机号格式
        # redis_conn.setex('sms_%s' % mobile, IMAGE_CODE_EXPIRE, sms_code)
        pl.setex('sms_%s' % mobile, IMAGE_CODE_EXPIRE, sms_code)

        # 当手机号发过了验证码，向Redis存储一个发送过的标记
        # 可能存在没存进去的问题，这时候可以使用ttl获取一下那个300秒的验证码，时间够不够300-60秒
        pl.setex('send_flag_%s' % mobile, SEND_SMS_TIME, 1)

        # 执行管道
        pl.execute()

        # 利用容联云平台进行发送短信
        send_sms_code.delay(mobile, sms_code)   # 将发短信的函数内存添加到仓库中，让worker去新的线程执行

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
