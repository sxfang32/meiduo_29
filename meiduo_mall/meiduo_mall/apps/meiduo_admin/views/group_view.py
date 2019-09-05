from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from django.contrib.auth.models import Group
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.group_serializer import *
from meiduo_admin.serializers.perm_serializer import *


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
    pagination_class = MyPage


class PermSimpleView(ListAPIView):
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermSerializer
