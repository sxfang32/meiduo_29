from django.shortcuts import render
from django import http
from django.views import View
from django.core.cache import cache

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
            # 从缓存中获取所有数据
            province_list = cache.get('province_list')
            if province_list is None:
                # province_qs = Area.objects.filter(parent__isnull=True)
                province_qs = Area.objects.filter(parent_id=None)
                province_list = []  # 用来装所有省的字典格式数据
                for province_model in province_qs:
                    province_list.append({
                        "id": province_model.id,
                        "name": province_model.name
                    })

                # 把所有省数据缓存到redis
                cache.set('province_list', province_list, 3600)
            return http.JsonResponse({"code": RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            # 如果有area_id，就是要查询指定id的下级所有行政区
            # 查询下级行政区
            sub_data = cache.get('subs_%s' % area_id)
            if sub_data is None:
                try:
                    parent_model = Area.objects.get(id=area_id)
                except Area.DoesNotExist:
                    return http.HttpResponseForbidden("area_id不存在")
                # 通过上级查询出所有下级行政区
                sub_qs = parent_model.subs.all()

                sub_list = []  # 用来装所有下级行政区
                for sub_model in sub_qs:
                    sub_list.append({
                        'id': sub_model.id,
                        'name': sub_model.name
                    })

                    # 定义字典变量，包装前端需要的数据
                sub_data = {
                    'id': parent_model.id,
                    'name': parent_model.name,
                    'subs': sub_list
                }

                # 缓存下级行政区数据
                cache.set('subs_%s' % area_id, sub_data, 3600)

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})

