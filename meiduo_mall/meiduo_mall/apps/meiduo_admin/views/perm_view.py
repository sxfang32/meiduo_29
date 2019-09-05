from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from django.contrib.auth.models import Permission
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.perm_serializer import *


class PermViewSet(ModelViewSet):
    queryset = Permission.objects.all().order_by('pk')
    serializer_class = PermSerializer
    pagination_class = MyPage


class PermTypeView(ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = PermTypeSerializer
