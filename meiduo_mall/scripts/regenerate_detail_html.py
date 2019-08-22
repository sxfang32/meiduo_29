#!/usr/bin/env python  # 使用当前项目指定或终端进入  #也可以用绝对路径指定虚拟环境中的解释权
import sys


sys.path.insert(0, '../')

import os
# 指定Django配置模块路径
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

import django
# 启动Django
django.setup()

from django.template import loader
from django.conf import settings
from goods.models import SKU

from goods import models
from contents.utls import get_categories
from goods.utils import get_breadcrumb


def generate_static_sku_detail_html(sku_id):
    """
    生成静态商品详情页面
    :param sku_id: 商品sku id
    """
    sku = SKU.objects.get(id=sku_id)

    category = sku.category
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

    template = loader.get_template('detail.html')
    html_text = template.render(context)
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'detail/'+str(sku_id)+'.html')
    with open(file_path, 'w') as f:
        f.write(html_text)

if __name__ == '__main__':
    skus = models.SKU.objects.all()
    for sku in skus:
        print(sku.id)
        generate_static_sku_detail_html(sku.id)