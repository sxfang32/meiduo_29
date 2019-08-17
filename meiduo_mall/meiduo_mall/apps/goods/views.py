from django.shortcuts import render
from django.views import View
from contents.utls import get_categories
from .models import GoodsCategory
from django import http

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




        context = {
            'categories': get_categories(),  # 频道分类
            'breadcrumb': breadcrumb, # 面包屑导航
            'sort': '',# 排序字段
            'category': '', # 第三级分类
            'page_skus': '',  # 分页后的数据
            'total_page': '', # 总页数
            'page_num': page_num  # 翻页数
        }
        return render(request, 'list.html', context)