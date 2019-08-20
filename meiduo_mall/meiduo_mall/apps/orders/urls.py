from django.conf.urls import url
from . import views
urlpatterns = [
    # 结算预览页面
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view())
]