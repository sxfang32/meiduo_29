from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from meiduo_admin.views.home_view import HomeView, GoodsVisitCountView
from meiduo_admin.views.user_view import *
from meiduo_admin.views.sku_view import *
from meiduo_admin.views.spu_view import *
from meiduo_admin.views.spec_view import *
from meiduo_admin.views.option_view import *
from meiduo_admin.views.channel_view import *
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
    url(r'^skus/(?P<pk>\d+)/$', SKUViewSet.as_view({'get': 'retrieve', "delete": "destroy", "put": "update"})),

    # 获得新建sku可选三级分类
    url(r'^skus/categories/$', GoodsCategoryView.as_view()),

    # 获得新建sku可选spu
    url(r'^goods/simple/$', SPUSimpleView.as_view()),

    # 获得spu可选规格及选项信息
    url(r'^goods/(?P<pk>\d+)/specs/$', SPUSpecOptView.as_view()),

    # spu管理
    # url(r'^goods/$', SPUViewSet.as_view({'get': 'list', "post": "create"})),
    # url(r'^goods/(?P<pk>\d+)/$', SPUViewSet.as_view({'get': 'retrieve', "put": "update", "delete": "destroy"})),

    # 获得新知spu可选品牌信息
    url(r'^goods/brands/simple/$', SPUViewSet.as_view({'get': 'spu_brands'})),

    # 获得新增spu可选一级分类信息
    url(r'^goods/channel/categories/$', SPUCategoryView.as_view()),

    # 获得新增spu可选二、三级分类信息
    url(r'^goods/channel/categories/(?P<pk>\d+)/$', SPUCategoryView.as_view()),

    # 选项表管理
    url(r'^specs/options/$', OptViewSet.as_view({"get": "list", "post": "create"})),

    url(r'^specs/options/(?P<pk>\d+)/$', OptViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),

    # 获得新增选项可选规格信息
    url(r'^goods/specs/simple/$', OptSpecView.as_view()),

    # 频道管理
    url(r'^goods/channels/$', ChannelViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^goods/channels/(?P<pk>\d+)/$',
        ChannelViewSet.as_view({"get": "retrieve", "delete": "destroy", "put": "update"})),

    # 新建频道可选一级分类信息
    url(r'^goods/categories/$', SPUCategoryView.as_view()),

    # 新建频道可选分组信息
    url(r'^goods/channel_types/$', ChannelGroupView.as_view()),
]

# 路由对象只需要有一个
# 可以使用该对象，多次对不同的视图集进行注册
router = SimpleRouter()
router.register(prefix='statistical', viewset=HomeView, base_name='home')
router.register(prefix='goods/specs', viewset=SpecViewSet, base_name='spec')
router.register(prefix='goods', viewset=SPUViewSet, base_name='spu')
urlpatterns += router.urls
