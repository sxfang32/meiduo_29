import json, pickle, base64
from django import http
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

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
            """
            hash:{sku_id_1: 1}
            set: {sku_id_1}
            """

            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # hincrby：如果sku_id, 就自动做增量，不存在就新增
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            # 判断当前是否勾选，勾选就把sku_id添加到set sadd
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)

            pl.execute()

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})

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

                # cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

                # 判断当前要添加的商品是否之前已经添加过，如果添加过应该累加count
                if sku_id in cart_dict:
                    origin_count = cart_dict[sku_id]['count']
                    count += origin_count

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

    def get(self, request):
        """购物车查询"""
        user = request.user
        if user.is_authenticated:
            # 登录用户从redis获取购物车数据
            """
                hash:{sku_id_1: 1}
                set: {sku_id_1}
            """
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            # 获取hash数据
            redis_carts = redis_conn.hgetall('cart_%s' % user.id)
            # 获取set数据
            selected_ids = redis_conn.smembers('selected_%s' % user.id)
            # 将redis购物车数据格式转换成和cookie的购物车数据一致
            cart_dict = {}  # 用来包装redis购物车的所有数据
            for sku_id_bytes in redis_carts:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(redis_carts[sku_id_bytes]),
                    'selected': sku_id_bytes in selected_ids
                }

        else:
            # 未登录用户从cookie获取购物车数据
            """
           {
             'sku_id_1':{'count':1,'selectes':True},
             'sku_id_2':{'count':1,'selectes':True}
           }
           """
            # 获取cookie中的购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断是否获取到
            if cart_str:
                # 将cart_str转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return render(request, 'cart.html')

        # 查询并包装购物车展示时所需要的数据
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())
        # 定义一个用来包装所有购物车字典的列表
        sku_list = []
        # 遍历sku_qs，进行模型转字典
        for sku_model in sku_qs:
            # 获取当前商品的count
            count = cart_dict[sku_model.id]['count']
            sku_list.append({
                'id': sku_model.id,
                'name': sku_model.name,
                'default_image_url': sku_model.default_image.url,
                'price': str(sku_model.price),  # 转成str是为了方便js中进行解析
                'count': count,
                'selected': str(cart_dict[sku_model.id]['selected']),
                'amount': str(sku_model.price * count)
            })
        context = {'cart_skus': sku_list}
        return render(request, 'cart.html', context)

    def put(self, request):
        """购物车修改"""
        # 1.接收请求体中非表单数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected')

        # 2.校验
        if all([sku_id, count]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
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

        # 获取本次修改的商品sku模型
        sku_model = SKU.objects.get(id=sku_id)
        cart_sku = {
            'id': sku_model.id,
            'name': sku_model.name,
            'default_image_url': sku_model.default_image.url,
            'price': str(sku_model.price),  # 转成str是为了方便js中进行解析
            'count': count,
            'selected': selected,
            'amount': str(sku_model.price * count)
        }
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改购物车成功', 'cart_sku': cart_sku})

        # 判断登录
        user = request.user
        if user.is_authenticated:
            # 登录用户修改redis
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 修改hash中指定key对应 count
            pl.hset('cart_%s' % user.id, sku_id, count)
            # 判断当前商品是要勾选还是不勾选
            if selected:
                # 勾选就将当前sku_id添加到set
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                # 不勾选就将sku_id 从 set 移除
                pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

        else:
            # 未登录用户修改cookie
            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')

            # 判断是否获取到cookie购物车数据
            if cart_str:

                # 如果取到了将cart_str转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有获取到cookie购物车数据，提前响应
                return http.JsonResponse({"code": RETCODE.NODATAERR, 'errmsg': '没有获取到数据'})

            # 覆盖cookie大字典中指定键值对
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将字典转回字符串
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 创建响应对象设置cookie
            response.set_cookie('carts', cart_str)
            # 响应
        return response

    def delete(self, request):
        """购物车删除"""

        # 1.接收请求体中非表单数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 2.校验
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id无效')

        # 获取user
        user = request.user
        # 判断登录
        if user.is_authenticated:
            # 登录操作redis
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')

            # 创建管道
            pl = redis_conn.pipeline()
            # 删除hash数据
            pl.hdel('cart_%s' % user.id, sku_id)
            # 删除set
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除商品成功'})
        else:
            # 未登录用户
            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断是否获取到cookie购物车数据
            if cart_str:
                # cart_str 转 cart_dict
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 提前响应
                return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有获取到数据'})

            # 判断当前要删除的sku_d在cookie大字典中是否存在
            if sku_id in cart_dict:
                # del 删除字典中指定的键值对
                del cart_dict[sku_id]

            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
            # 判断cookie购物车中字典是否已经空了
            if not cart_dict:
                # 如果cookie购物车数据已经删除干净了，直接将浏览器上的cookie购物车数据删除
                response.delete_cookie('carts')
                return response
            # 将 cart_dict 转 cart_str
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 设置cookie
            response.set_cookie('carts', cart_str)

            return response


class CartsSelectedAllView(View):
    """购物车全选"""

    def put(self, request):

        # 接收请求体数据
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')
        # 校验
        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('数据类型有误')

        user = request.user
        if user.is_authenticated:
            # 登录用户操作redis
            redis_conn = get_redis_connection('carts')
            # 判断是全选还是取消全选
            if selected:
                # 全选：将hash中所有的sku_id添加到set
                redis_cart = redis_conn.hgetall('cart_%s' % user.id)
                sku_ids = redis_cart.keys()
                redis_conn.sadd('selected_%s' % user.id, *sku_ids)
            else:
                # 取消全选：将set集合直接删除
                redis_conn.delete('selected_%s' % user.id)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选成功'})
        else:
            # 未登录用户才做cookie
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '没有获取到数据'})

            # 遍历购物车大字典
            for sku_id in cart_dict:
                # 将里面的每个小字典的selected改为True or False
                cart_dict[sku_id]['selected'] = selected

            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选成功'})
            response.set_cookie('carts', cart_str)
            return response


class CartSimpleView(View):
    """展示简单购物车"""

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            # 登录用户从redis获取购物车数据
            """
                hash:{sku_id_1: 1}
                set: {sku_id_1}
            """
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            # 获取hash数据
            redis_carts = redis_conn.hgetall('cart_%s' % user.id)
            # 获取set数据
            selected_ids = redis_conn.smembers('selected_%s' % user.id)
            # 将redis购物车数据格式转换成和cookie的购物车数据一致
            cart_dict = {}  # 用来包装redis购物车的所有数据
            for sku_id_bytes in redis_carts:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(redis_carts[sku_id_bytes]),
                    'selected': sku_id_bytes in selected_ids
                }

        else:
            # 未登录用户从cookie获取购物车数据
            """
           {
             'sku_id_1':{'count':1,'selectes':True},
             'sku_id_2':{'count':1,'selectes':True}
           }
           """
            # 获取cookie中的购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断是否获取到
            if cart_str:
                # 将cart_str转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return render(request, 'cart.html')

        # 查询并包装购物车展示时所需要的数据
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())
        # 定义一个用来包装所有购物车字典的列表
        sku_list = []
        # 遍历sku_qs，进行模型转字典
        for sku_model in sku_qs:
            # 获取当前商品的count
            count = cart_dict[sku_model.id]['count']
            sku_list.append({
                'id': sku_model.id,
                'name': sku_model.name,
                'default_image_url': sku_model.default_image.url,
                'count': count,
            })

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg':'OK','cart_skus':sku_list})