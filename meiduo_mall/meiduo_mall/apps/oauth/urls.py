from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
    url(r'^oauth_callback/$', views.QQAuthUserView.as_view()),
]