from django.conf.urls import url
from . import views
urlpatterns = [
    # 结算预览页面
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    url(r'^orders/commit/$', views.OrderCommitView.as_view()),
    url(r'^orders/success/$', views.OrderSuccessView.as_view()),
    url(r'^orders/info/(?P<page_num>\d+)/$', views.UserCenterOrder.as_view()),
]