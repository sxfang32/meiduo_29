from rest_framework.views import APIView
from meiduo_admin.serializers.login_serializer import *
from rest_framework.response import Response


# 定义登录视图，使用序列化器完成，响应请求

class LoginView(APIView):

    def post(self, request):
        """后台登录功能"""
        # 1.构建序列化器，传入前端数据
        s = LoginSerializer(data=request.data)
        # 2.校验数据
        s.is_valid(raise_exception=True)
        # 3.得到有效数据，构建响应对象
        return Response({
            "token": s.validated_data['token'],
            "username": s.validated_data['user'].username,
            "user_id": s.validated_data['user'].id
        })
