from rest_framework import serializers
from users.models import User
from django.contrib.auth.hashers import make_password


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'password']
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate(self, attrs):
        # 1.attrs缺少is_staff=True
        # 2.attrs密码是明文的
        attrs['is_staff'] = True
        attrs['password'] = make_password(attrs['password'])

        return attrs

    # def create(self, validated_data):
    #     return User.objects.create_superuser(**validated_data)
