from django.conf.urls import url
from . import views
urlpatterns = [
    # 商品列表页
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view()),
    # 商品热销排行
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodView.as_view()),
    # 商品详情页面
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view()),
    # 商品详情类型每日访问量统计
    url(r'^visit/(?P<category_id>\d+)/$', views.DeatilVisitView.as_view()),
    # 商品详情页获取评价
    url(r'^comments/(?P<sku_id>\d+)/$', views.GoodsCommentView.as_view()),
]