from django.conf.urls import url
from . import views

urlpatterns = [
    #获取微博登陆界面url
    url(r'^sina/authorization/$', views.WeiboAuthURLView.as_view()),
    url(r'^wboauth_callback/$', views.WeiboAuthUserView.as_view()),
    url(r'^oauth/sina/user/$', views.ShowPageView.as_view()),
]