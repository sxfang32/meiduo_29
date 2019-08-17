from django.shortcuts import render
from django.views import View
from contents.utls import get_categories
from .models import GoodsCategory, SKU
from django import http
from django.core.paginator import Paginator, EmptyPage
from goods.utils import get_breadcrumb
from meiduo_mall.utils.response_code import RETCODE


class ListView(View):
    """商品列表界面"""

    def get(self, request, category_id, page_num):

        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('类别ID不存在')

        # cat1 = cat3.parent.parent
        # # 给一级类别定义URL属性
        # cat1.url = cat1.goodschannel_set.all()[0].url
        #
        # # 包装面包屑导航数据
        # breadcrumb = {
        #     'cat1': cat3.parent.parent,
        #     'cat2': cat3.parent,
        #     'cat3': cat3
        # }

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
            'breadcrumb': get_breadcrumb(cat3),  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': cat3,  # 第三级分类
            'page_skus': page_skus,  # 分页后的数据
            'total_page': total_page,  # 总页数
            'page_num': page_num  # 当前页码
        }
        return render(request, 'list.html', context)


class HotGoodView(View):

    def get(self, request, category_id):

        # 1.校验
        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('商品类别不存在')

        # 2.根据指定三级类别查询出销量最好的前两个商品
        # sku_qs = cat3.sku_set.filter(is_launched=True).order_by('-sales')[:2]
        sku_qs = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]

        # 3.sku模型转字典
        skus = []
        for sku_model in sku_qs:
            skus.append(
                {
                    'id': sku_model.id,
                    'name': sku_model.name,
                    'price': sku_model.price,
                    'defult_image_url': sku_model.default_image.url
                }
            )

        # 4.响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': skus})


class DetailView(View):
    """商品详情页"""

    def get(self, request, sku_id):

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        category = sku.category  # 获取当前sku所对应的三级分类

        # 查询当前sku所对应的spu
        spu = sku.spu

        """1.准备当前商品的规格选项列表 [8, 11]"""
        # 获取出当前正显示的sku商品的规格选项id列表
        current_sku_spec_qs = sku.specs.order_by('spec_id')
        current_sku_option_ids = []  # [8, 11]
        for current_sku_spec in current_sku_spec_qs:
            current_sku_option_ids.append(current_sku_spec.option_id)

        """2.构造规格选择仓库
        {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        """
        # 构造规格选择仓库
        temp_sku_qs = spu.sku_set.all()  # 获取当前spu下的所有sku
        # 选项仓库大字典
        spec_sku_map = {}  # {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        for temp_sku in temp_sku_qs:
            # 查询每一个sku的规格数据
            temp_spec_qs = temp_sku.specs.order_by('spec_id')
            temp_sku_option_ids = []  # 用来包装每个sku的选项值
            for temp_spec in temp_spec_qs:
                temp_sku_option_ids.append(temp_spec.option_id)
            spec_sku_map[tuple(temp_sku_option_ids)] = temp_sku.id

        """3.组合 并找到sku_id 绑定"""
        spu_spec_qs = spu.specs.order_by('id')  # 获取当前spu中的所有规格

        for index, spec in enumerate(spu_spec_qs):  # 遍历当前所有的规格
            spec_option_qs = spec.options.all()  # 获取当前规格中的所有选项
            temp_option_ids = current_sku_option_ids[:]  # 复制一个新的当前显示商品的规格选项列表
            for option in spec_option_qs:  # 遍历当前规格下的所有选项
                temp_option_ids[index] = option.id  # [8, 12]
                option.sku_id = spec_sku_map.get(tuple(temp_option_ids))  # 给每个选项对象绑定下他sku_id属性

            spec.spec_options = spec_option_qs  # 把规格下的所有选项绑定到规格对象的spec_options属性上

        context = {
            'categories': get_categories(),  # 商品分类
            'breadcrumb': get_breadcrumb(category),  # 面包屑导航
            'sku': sku,  # 当前要显示的sku模型对象
            'category': category,  # 当前的显示sku所属的三级类别
            'spu': spu,  # sku所属的spu
            'spec_qs': spu_spec_qs,  # 当前商品的所有规格数据
        }

        return render(request, 'detail.html', context)
