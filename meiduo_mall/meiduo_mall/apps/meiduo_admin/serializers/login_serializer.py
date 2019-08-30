from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler


# 定义一个序列化器
# 完成数据校验（username,password）
# 校验通过签发token


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs['username']
        password = attrs['password']
        # 1.传统认证用户名密码
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError('传统认证不通过')

        # 签发token
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return {
            "user": user,
            "token": token
        }
