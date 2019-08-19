import json, pickle, base64
from django import http
from django.shortcuts import render
from django.views import View


from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE


class CartsView(View):
    """购物车"""

    def post(self, request):
        """购物车新增"""

        # 1.接收请求体中非表单数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2.校验
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id无效')

        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('数据类型有误')

        # 判断selected是否布尔类型对象
        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('数据类型有误')

        # 3.判断是否登录
        user = request.user
        if user.is_authenticated:
            # 3.1登录用户操作Redis购物车
            pass
        else:
            # 3.2非登录用户操作cookie购物车
            # 先尝试从cookie中获取购物车数据
            cart_str = request.COOKIES.get('carts')

            """
            {
              'sku_id_1':{'count':1,'selectes':True},
              'sku_id_2':{'count':1,'selectes':True}
            }
            """
            # 判断是否获取到cookie购物车数据
            if cart_str:
                # 如果取到将cookie购物车数据，要将str转换回字典
                cart_str_bytes = cart_str.encode()
                cart_byte = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_byte)

                # 判断当前要添加的商品是否之前已经添加过，如果添加过应该累加count
                if sku_id in cart_dict:
                    origin_count = cart_dict[sku_id]['count']
                    count += origin_count

                # cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

            else:
                # 如果还没有cookie购物车数据，定义一个新字典用来添加购物车数据
                cart_dict = {}

            # 添加或修改
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将字典转换回字符串
            cart_byte = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_byte)
            cart_str = cart_str_bytes.decode()

            # 设置cookie
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
            response.set_cookie('carts', cart_str)

            # 响应
            return response

        pass












    def get(self, request):
        """购物车查询"""
        pass

    def put(self, request):
        """购物车修改"""
        pass

    def delete(self, request):
        """购物车删除"""
        pass
