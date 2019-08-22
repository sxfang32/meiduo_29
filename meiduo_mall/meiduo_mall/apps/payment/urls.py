from django.conf.urls import url
from . import views
urlpatterns = [
    # 结算预览页面
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentURLView.as_view()),
    url(r'^payment/status/$', views.PaymentURLView.as_view()),
]