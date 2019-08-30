from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from meiduo_admin.views.login_view import LoginView

urlpatterns = [
    # 用户登录接口
    # url(r'authorizations/', LoginView.as_view()),
    url(r'authorizations/', obtain_jwt_token),

]
