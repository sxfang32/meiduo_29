from django.shortcuts import render
from django.views import View

from goods.models import GoodsCategory, GoodsChannel
from .utls import get_categories
from .models import Content, ContentCategory


class IndexView(View):
    """展示首页"""

    def get(self, request):
        """提供首页广告界面"""

        contents = {}  # 用来包装所有广告数据
        # 查询所有广告类别数据
        content_cat_qs = ContentCategory.objects.all()
        # 遍历广告类型查询集，来进行包装数据
        for content_cat in content_cat_qs:
            # 将每种类别下的所有广告查询出来(一查多)，作为字典的value
            contents[content_cat.key] = content_cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories': get_categories(),  # 商品分类数据
            'contents': contents   # 广告数据
        }

        return render(request, 'index.html', context)
