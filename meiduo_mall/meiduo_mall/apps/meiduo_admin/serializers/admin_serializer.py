from rest_framework import serializers
from users.models import User
from django.contrib.auth.hashers import make_password


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'mobile',

            'password',
            'groups',
            'user_permissions',
        ]
        extra_kwargs = {
            'password': {"write_only": True},
            # 'groups': {"write_only": True},
            # 'user_permissions': {"write_only": True}
        }

    def validate(self, attrs):
        # 密码加密
        # 超级管理员
        attrs['password'] = make_password(attrs['password'])
        attrs['is_staff'] = True
        return attrs
