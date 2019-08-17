from django.shortcuts import render
from django.views import View
from contents.utls import get_categories
from .models import GoodsCategory
from django import http
from django.core.paginator import Paginator

class ListView(View):
    """商品列表界面"""

    def get(self, request, category_id, page_num):

        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('类别ID不存在')

        cat1 = cat3.parent.parent
        cat1.url = cat1.goodschannel_set.all()[0].url

        # 包装面包屑导航数据
        breadcrumb = {
            'cat1': cat3.parent.parent,
            'cat2': cat3.parent,
            'cat3': cat3
        }


        # 查询指定三级类别下的所有SKU
        sku_qs = cat3.sku_set.filter(is_launched=True)
        # 每页显示5条数据:计算总页数 page = total_count / 5 + (1 if total % 5 else 0)
        # sa = 5 * (page_num - 1)
        # sku_qs[sa : (sa + (5 - 1))]  # 计算显示指定页的角标

        context = {
            'categories': get_categories(),  # 频道分类
            'breadcrumb': breadcrumb, # 面包屑导航
            'sort': '',# 排序字段
            'category': '', # 第三级分类
            'page_skus': '',  # 分页后的数据
            'total_page': '', # 总页数
            'page_num': page_num  # 当前页码
        }
        return render(request, 'list.html', context)