from django.shortcuts import render
from django.views import View

from goods.models import GoodsCategory, GoodsChannel


class IndexView(View):
    """展示首页"""

    def get(self, request):
        """提供首页广告界面"""

        # 定义一个变量用来包装所有商品分类数据
        categories = {}

        # 获取商品类别分组表中的数据
        goods_channel_qs = GoodsChannel.objects.order_by('group_id', 'sequence')

        # 遍历goods_channel_qs 查询集 将数据向categories添加及构造
        for goods_channel_model in goods_channel_qs:
            # 获取当前组的ID
            group_id = goods_channel_model.group_id
            # 每一组只包装一次初始结构 数据
            if group_id not in categories:
                categories[group_id] = {
                    'channels': [],  # 包装当前组下面的所有一级
                    'sub_cats': [],  # 包装当前组下面的所有二级
                }

            # 查询对应的一级商品类别数据
            cat1 = goods_channel_model.category
            # 将商品频道表中的url还给对应的一级类别模型
            cat1.url = goods_channel_model.url

            # 将当前组中的一级模型对象添加到列表中
            categories[group_id]['channels'].append(cat1)

            # 查询出当前一级下面的所有二级
            cat2_qs = cat1.subs.all()

            # 遍历二级类别查询集，给每个二级商多定义一个属性，保存它的三级
            for cat2 in cat2_qs:
                # 查询指定二级下面的所有三级
                cat3_qs = cat2.subs.all()
                # 将当前二级下的所有三级保存到对应二级的一个自定义属性上
                cat2.sub_cats = cat3_qs
                categories[group_id]['sub_cats'].append(cat2)

        context = {
            'categories': categories,
            'contents': '广告数据'
        }

        return render(request, 'index.html', context)
