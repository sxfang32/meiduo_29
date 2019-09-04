"""
Django settings for meiduo_mall project.

Generated by 'django-admin startproject' using Django 1.11.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
import datetime
import os, sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 追加系统导包路径
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
# 以后在导包/模板时，apps中的就必须基于apps导包路径，其他全部基于外层meiduo_mall

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'enh#zx8+1+1^j#h@z7(*xy5vs^-hwaijq0wyd-eh&l#lfh$31$'

# SECURITY WARNING: don't run with debug turned on in production!
# 默认开启调试模式：代码修改会自动重启，只有调试模式Django才提供静态文件访问支持
DEBUG = True

ALLOWED_HOSTS = ['www.meiduo.site', '127.0.0.1']

# Application definition

# 注册和安装应用
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 只有当应用中用到模型需求迁移建表， 或应用中使用了模板时才需要注册，如果应用中只有视图和路由这些代码，应用可以不用注册。
    'users.apps.UsersConfig',  # 用户模块
    'oauth.apps.OauthConfig',  # QQ模块
    'areas.apps.AreasConfig',  # 省市区模块
    'contents.apps.ContentsConfig',  # 首页模块
    'goods.apps.GoodsConfig',  # 商品模块
    'orders.apps.OrdersConfig',  # 订单模块
    'payment.apps.PaymentConfig',  # 支付宝模块
    'weibo.apps.WeiboConfig',  # 微博模块

    'haystack',
    'django_crontab',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 路由入口配置
ROOT_URLCONF = 'meiduo_mall.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',  # 指定模板引擎
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # 指定模板文件路径
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            # 补充jinja2模板引擎黄精
            'environment': 'meiduo_mall.utils.jinja2_env.jinja2_environment',
        },
    },
]

WSGI_APPLICATION = 'meiduo_mall.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {  # 写（主机）
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '192.168.27.128',  # 数据库主机
        'PORT': 3306,  # 数据库端口
        'USER': 'meiduo_29',  # 数据库用户名
        'PASSWORD': 'meiduo_29',  # 数据库用户密码
        'NAME': 'meiduo_29'  # 数据库名字

    },
    'slave': {  # 读（从机）
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '192.168.27.128',
        'PORT': 8306,
        'USER': 'root',
        'PASSWORD': 'mysql',
        'NAME': 'meiduo_29'
    }
}

# redis数据库
CACHES = {
    "default": {  # 默认
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.27.128:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "session": {  # session
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.27.128:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "verify_codes": {  # 验证码
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.27.128:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "history": {  # 用户浏览记录
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.27.128:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "carts": {  # 购物车
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.27.128:6379/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "order": {  # 订单
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.27.128:6379/5",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}

# 指定session存储方案
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True
# USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

# 静态文件访问路由前端
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# 日志输出
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.path.dirname(BASE_DIR), 'logs/meiduo.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}

# 指定认证模型类
# 指定模型类时，必须以应用名.类名的方式指定
AUTH_USER_MODEL = 'users.User'
# 指定登录认证类
AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileAuthBackend']

LOGIN_URL = '/login/'

# QQ登录配置
QQ_CLIENT_ID = '101518219'
QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'
QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'

# 邮件服务配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 指定邮件后端
EMAIL_PORT = 25  # 发邮件端口

EMAIL_HOST = 'smtp.163.com'  # 发邮件主机
EMAIL_HOST_USER = 'itcast99@163.com'  # 授权的邮箱
EMAIL_HOST_PASSWORD = 'python99'  # 邮箱授权时获得的密码，非注册登录密码
EMAIL_FROM = '美多商城<itcast99@163.com>'  # 发件人抬头

EMAIL_VERIFY_URL = 'http://www.meiduo.site:8000/emails/verification/'

# 指定远程图片文件的绝对路径前半段（路由）
# MEDIA_URL = 'http://192.168.27.128:8888/'

# 修改Django的文件存储类
# 所有文件类型字段在保存新建或更新的时候，会自动调用该后端实现。
DEFAULT_FILE_STORAGE = 'meiduo_mall.utils.fastdfs.fdfs_storage.FastDFSStorage'

# 指定远程图片文件的绝对路径前半段（路由）
FDFS_BASE_URL = 'http://image.meiduo.site:8888/'

FDFS_CONF_PATH = os.path.join(BASE_DIR, 'utils', 'fastdfs', 'client.conf')

# 支付宝
ALIPAY_APPID = '2016101400684429'
ALIPAY_DEBUG = True  # 表示是沙箱环境还是真实支付环境
ALIPAY_URL = 'https://openapi.alipaydev.com/gateway.do'
ALIPAY_RETURN_URL = 'http://www.meiduo.site:8000/payment/status/'

# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://192.168.27.128:9200/',  # Elasticsearch服务器ip地址，端口号固定为9200
        'INDEX_NAME': 'meiduo_mall',  # Elasticsearch建立的索引库的名称
    },
}

# 当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# 分页数量
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 5

CRONJOBS = [
    # 每1分钟生成一次首页静态文件
    ('*/1 * * * *', 'contents.crons.generate_static_index_html',
     '>> ' + os.path.join(os.path.dirname(BASE_DIR), 'logs/crontab.log'))
]

# 解决页面静态化编码问题
CRONTAB_COMMAND_PREFIX = 'LANG_ALL=zh_cn.UTF-8'

# 指定数据文件
DATABASE_ROUTERS = ['meiduo_mall.utils.db_router.MasterSlaveDBRouter']

# 静态文件收集目录
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static')

# #微博登录配置
APP_KEY = '3889171625'
APP_SECRET = '855350448d4b0d1578315b4060f319e8'
REDIRECT_URI = 'http://www.meiduo.site:8000/wboauth_callback'

# CORS
CORS_ORIGIN_WHITELIST = (
    'http://127.0.0.1:8080',
    'http://localhost:8080',
    'http://www.meiduo.site:8080',
    'http://api.meiduo.site:8000'
)
CORS_ALLOW_CREDENTIALS = True  # 允许携带cookie

# 身份认证
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',  # 签发、验证
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=100),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'meiduo_mall.apps.meiduo_admin.utils.jwt_response_cutom_handler'
}
