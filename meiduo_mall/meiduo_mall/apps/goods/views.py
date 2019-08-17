from django.shortcuts import render
from django.views import View
from contents.utls import get_categories
from .models import GoodsCategory
from django import http
from django.core.paginator import Paginator,EmptyPage


class ListView(View):
    """商品列表界面"""

    def get(self, request, category_id, page_num):

        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('类别ID不存在')

        cat1 = cat3.parent.parent
        # 给一级类别定义URL属性
        cat1.url = cat1.goodschannel_set.all()[0].url

        # 包装面包屑导航数据
        breadcrumb = {
            'cat1': cat3.parent.parent,
            'cat2': cat3.parent,
            'cat3': cat3
        }

        # 获取查询参数中的排序规则
        sort = request.GET.get('sort')
        if sort == 'price':
            sort_filed = 'price'
        elif sort == 'hot':
            sort_filed = 'sales'
        else:
            sort = 'default'
            sort_filed = 'create_time'

        # 查询指定三级类别下的所有SKU
        sku_qs = cat3.sku_set.filter(is_launched=True).order_by(sort_filed)

        # 每页显示5条数据:计算总页数 page = total_count / 5 + (1 if total % 5 else 0)
        # sa = 5 * (page_num - 1)
        # sku_qs[sa : (sa + (5 - 1))]  # 计算显示指定页的角标

        paginator = Paginator(sku_qs, 5)  # 创建一个分页对象
        try:
            page_skus = paginator.page(page_num)  # 返回指定页的数据
        except EmptyPage:
            return http.HttpResponseForbidden('没有下一页，别点了')
        total_page = paginator.num_pages  # 获取总页数

        context = {
            'categories': get_categories(),  # 频道分类
            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': cat3,  # 第三级分类
            'page_skus': page_skus,  # 分页后的数据
            'total_page': total_page,  # 总页数
            'page_num': page_num  # 当前页码
        }
        return render(request, 'list.html', context)
