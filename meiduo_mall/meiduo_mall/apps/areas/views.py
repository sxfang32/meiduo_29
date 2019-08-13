from django.shortcuts import render
from django import http
from django.views import View

from meiduo_mall.utils.response_code import RETCODE
from .models import Area


class AreasView(View):
    """省市区数据查询"""

    def get(self, request):
        # 获取area_id查询参数
        area_id = request.GET.get('area_id')
        # 判断是否传递了area_id，如果没有，说明要是查询说有省的数据
        if area_id is None:
            # 查询所有省
            # province_qs = Area.objects.filter(parent__isnull=True)
            province_qs = Area.objects.filter(parent_id=None)
            province_list = []  # 用来装所有省的字典格式数据
            for province_model in province_qs:
                province_list.append({
                    "id": province_model.id,
                    "name": province_model.name
                })
            return http.JsonResponse({"code": RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            # 如果有，就是要查询指定id的下级所有行政区
            # 查询下级行政区
            pass
        pass
