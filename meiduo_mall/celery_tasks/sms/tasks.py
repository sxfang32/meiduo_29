# 编写任务代码的py文件
from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks.main import celery_app


@celery_app.task()      # 只有用此装饰器装饰过的函数才能成为celery任务
def send_sms_code(mobile, sms_code):
    """
    发短信的异步任务
    :param mobile: 要收短信的手机号
    :param sms_code: 短信验证码
    :return:
    """
    # 利用容联云平台发送短信
    # CCP().send_template_sms(手机号, [验证码, 过期时间：分钟], 使用的短信模板ID)
    CCP().send_template_sms(mobile, [sms_code, 5], 1)