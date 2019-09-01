from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from meiduo_admin.views.home_view import HomeView, GoodsVisitCountView
from meiduo_admin.views.user_view import *
from meiduo_admin.views.login_view import *
from meiduo_admin.views.sku_view import *
from rest_framework.routers import SimpleRouter

urlpatterns = [
    # 用户登录接口
    # url(r'authorizations/', LoginView.as_view()),
    url(r'^authorizations/', obtain_jwt_token),

    # 日分类访问量
    url(r'^statistical/goods_day_views/', GoodsVisitCountView.as_view()),

    # 序列化返回多个超级管理员对象
    url(r'^users/$', UserAPIView.as_view()),

    # SKU表管理
    url(r'^skus/$', SKUViewSet.as_view({'get': 'list', "post": "create"})),
    url(r'^skus/(?P<pk>\d+)/$', SKUViewSet.as_view({'get': 'retrieve', "post": "create", "delete": "destroy", "put": "update"})),

    # 获得新建sku可选三级分类
    url(r'^skus/categories/$', GoodsCategoryView.as_view()),

    # 获得新建sku可选spu
    url(r'^goods/simple/$', SPUSimpleView.as_view()),

    # 获得spu可选规格及选项信息
    url(r'^goods/(?P<pk>\d+)/specs/$', SPUSpecOptView.as_view()),
]

# 主页URL
# 1、用户总数统计
router = SimpleRouter()
router.register(prefix='statistical', viewset=HomeView, base_name='home')
urlpatterns += router.urls
