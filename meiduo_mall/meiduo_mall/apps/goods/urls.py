from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view()),
    # 商品热销排行
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodView.as_view()),
    # 商品详情页面
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view()),
    # 商品详情类型每日访问量统计
    url(r'^isit/(?P<category_id>\d+)/$', views.DeatilVisitView.as_view()),
]