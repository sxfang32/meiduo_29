from django.shortcuts import render
from django.views import View


class IndexView(View):
    """展示首页"""

    def get(self, request):
        """提供首页广告界面"""
        return render(request, 'index.html')
