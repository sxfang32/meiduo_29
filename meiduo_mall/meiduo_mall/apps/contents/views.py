from django.shortcuts import render
from django.views import View

from goods.models import GoodsCategory, GoodsChannel
from .utls import get_categories

class IndexView(View):
    """展示首页"""

    def get(self, request):
        """提供首页广告界面"""

        context = {
            'categories': get_categories(),
            'contents': '广告数据'
        }

        return render(request, 'index.html', context)
