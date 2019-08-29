# celery 程序启动文件，也是客户创建
from celery import Celery
import os

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

# 1.创建celery实例对象
celery_app = Celery('meiduo')

# 2.加载celery配置，指定谁来当消息队列
celery_app.config_from_object('celery_tasks.config')

# 3.注册任务，就是告诉celery它能生成什么任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email', 'celery_tasks.cancel_order'])
