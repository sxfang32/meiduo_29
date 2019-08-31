import json
from django import http
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import render
from django_redis import get_redis_connection
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
import logging
import re

from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address
from goods.models import SKU
from verifications import constants
from .models import OrderInfo, OrderGoods
from meiduo_mall.utils.response_code import RETCODE

logger = logging.getLogger('django')


class OrderSettlementView(LoginRequiredView):
    """结算预览界面"""

    def get(self, request):

        user = request.user
        # 查询当前登录用户的所有收货地址
        addresses = Address.objects.filter(user=user, is_deleted=False)

        # 判断是否有地址（使用三目运算）
        # addresses = addresses if addresses.exists() else None

        # 创建redis连接对象
        redis_conn = get_redis_connection('carts')
        # 获取hash 和 set 数据
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        selected_ids = redis_conn.smembers('selected_%s' % user.id)
        # 定义一个字典变量，用来保存已勾选商品的id和count
        cart_dict = {}
        for sku_id_bytes in selected_ids:
            cart_dict[int(sku_id_bytes)] = int(redis_cart[sku_id_bytes])

        # 查询所有要购买商品的sku模型
        skus = SKU.objects.filter(id__in=cart_dict.keys())

        # 赋予初始值
        total_count = 0  # 记录商品总数量
        total_amount = Decimal('0.00')  # 记录商品总金额

        # 遍历查询集，给每个sku模型多定义两个属性
        for sku in skus:
            sku.count = cart_dict[sku.id]
            sku.amount = sku.price * sku.count
            total_count += sku.count
            total_amount += (sku.amount)

        freight = Decimal('10.00')  # 哈哈这运费去到偏远地区怕是要亏死哦

        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }
        return render(request, 'place_order.html', context)


class OrderCommitView(LoginRequiredView):
    """提交订单"""

    def post(self, request):

        # 1.接收
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        user = request.user
        # 2.校验
        try:
            address = Address.objects.get(id=address_id, user=user, is_deleted=False)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id有误')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('支付方式错误')

        # # 生成订单编号：20190820145030+ user_id
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        # 单号存入Redis设置15分钟未付款自动关闭
        redis_conn = get_redis_connection('order')
        redis_conn.setex(order_id, constants.CANCEL_ORDER_TIME, "1")
        # redis_conn.setex(order_id, 20, "1")     # 测试阶段

        # 判断订单状态（三目运算法）
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                  if (pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY'])
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

        with transaction.atomic():  # 手动开启事务

            # 创建事务的保存点
            save_point = transaction.savepoint()
            try:
                # 3.存储一条订单基本信息记录（一）(OrderInfo)
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0.00'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status,
                )

                # 3.1获取购物车中redis数据
                # 创建连接对象
                redis_conn = get_redis_connection('carts')
                # 获取hash和set数据
                redis_cart = redis_conn.hgetall('cart_%s' % user.id)
                selected_ids = redis_conn.smembers('selected_%s' % user.id)
                # 定义一个字典用来装要购买的商品id和count
                cart_dict = {}
                for sku_id_bytes in selected_ids:
                    cart_dict[int(sku_id_bytes)] = int(redis_cart[sku_id_bytes])

                # 遍历要购买的商品大字典
                for sku_id in cart_dict:

                    while True:
                        # 获取sku模型
                        sku = SKU.objects.get(id=sku_id)
                        # 获取当前商品要购买的数量
                        buy_count = cart_dict[sku_id]
                        # 获取商品原有的库存和销量
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        # 判断库存
                        if buy_count > origin_stock:
                            # 回滚
                            transaction.savepoint_rollback(save_point)

                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        # 3.2 计算sku库存和销量
                        new_stock = origin_stock - buy_count
                        new_sales = origin_sales + buy_count

                        # # 修改sku库存和销量
                        # sku.stock = new_stock
                        # sku.sales = new_sales
                        # sku.save()

                        # 使用乐观锁解决同时下单的问题
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)
                        # 如果修改库存销量失败
                        if result == 0:
                            continue

                        # 3.3 修改spu
                        spu = sku.spu
                        spu.sales += buy_count
                        spu.save()

                        # 4.存储订单中商品信息记录（多）（OrderGood）
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=buy_count,
                            price=sku.price
                        )

                        # 累加购买商品总数量
                        order.total_count += buy_count
                        # 累加商品总价
                        order.total_amount += (sku.price * buy_count)

                        # 当执行到这时代表这个商品购买成功，跳出死循环
                        break

                # 累加运费一定要写在for外面
                order.total_amount += order.freight
                order.save()
            except Exception as error:
                logger.error(error)
                # 如果出现问题，就暴力回滚数据
                transaction.savepoint_rollback(save_point)
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '下单失败'})
            else:
                # 提交事务
                transaction.savepoint_commit(save_point)

        pl = redis_conn.pipeline()
        # 删除购物车中已被购买的商品
        pl.hdel('cart_%s' % user.id, *selected_ids)  # 将hash中已购买商品全部移除
        pl.delete('selected_%s' % user.id)  # 将set移除
        pl.execute()

        # 强调！这里不需要调用异步处理订单的函数，celery自己会处理！
        # event_handler(order_id)

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order_id})


class OrderSuccessView(LoginRequiredView):
    """展示订单提交成功页面"""

    def get(self, request):

        # 接收数据
        query_dict = request.GET
        order_id = query_dict.get('order_id')
        payment_amount = query_dict.get('payment_amount')
        pay_method = query_dict.get('pay_method')

        # 校验数据
        try:
            order = OrderInfo.objects.get(order_id=order_id, total_amount=payment_amount, pay_method=pay_method)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')

        # 展示数据
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }

        return render(request, 'order_success.html', context)


class UserCenterOrder(LoginRequiredView):
    """用户中心订单"""

    def get(self, request, page_num):

        if re.match("\d+", page_num) is False:
            return http.HttpResponseForbidden('参数错误')

        # 获取用户对象
        user = request.user
        # 查看当前登录用户所有订单和购买商品
        order_qs = OrderInfo.objects.filter(user_id=user.id).order_by('-create_time')
        # 遍历当前用户的订单表，以字典的形式将数据包装
        for order in order_qs:
            # 查询订单的所有商品
            sku_list = order.skus.all()
            # 遍历订单商品查询集
            for sku in sku_list:
                sku.default_image = sku.sku.default_image
                sku.name = sku.sku.name
                sku.price = sku.sku.price
                sku.amount = sku.price * sku.count
            order.sku_list = sku_list

            method_index = order.pay_method - 1
            status_index = order.status - 1
            # 给order添加pay_method_name和status_name属性
            order.pay_method_name = OrderInfo.PAY_METHOD_CHOICES[method_index][1]
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[status_index][1]

        # 分页功能
        paginator = Paginator(order_qs, 5)  # 创建一个分页对象
        try:
            page_skus = paginator.page(page_num)  # 返回指定页的数据
        except EmptyPage:
            return http.HttpResponseForbidden('没有下一页，别点了')
        total_page = paginator.num_pages  # 获取总页数

        context = {
            'page_orders': page_skus,
            'total_page': total_page,
            'page_num': page_num
        }

        # 将数据响应给前端

        return render(request, 'user_center_order.html', context)


class OrderCommentView(LoginRequiredView):
    """商品评论功能"""

    def get(self, request):
        # 接收参数
        order_id = request.GET.get('order_id')
        # 校验参数
        try:
            OrderGoods.objects.filter(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('参数有误')
        # 获取订单的所有未评价的商品
        order_goods = OrderGoods.objects.filter(order_id=order_id, is_commented=False)
        # 创建列表,包装每种商品的信息
        goods_list = []
        # 获取订单下的每种商品
        for goods in order_goods:
            goods_list.append({
                'name': goods.sku.name,
                'price': str(goods.price),
                'default_image_url': goods.sku.default_image.url,
                'order_id': goods.order_id,

                'sku_id': goods.sku_id,
                'display_score': goods.score,
                'comment': goods.comment,
                'is_anonymous': str(goods.is_anonymous)
            })
        # 渲染模板
        context = {
            'uncomment_goods_list': goods_list,
        }

        return render(request, 'goods_judge.html', context)

    def post(self, request):

        # 1.接收参数
        user = request.user
        json_dict = json.loads(request.body.decode())
        order_id = json_dict.get('order_id')
        sku_id = json_dict.get('sku_id')
        comment = json_dict.get('comment')
        score = json_dict.get('score')
        is_anonymous = json_dict.get('is_anonymous')
        # 2.校验参数
        if not all([order_id, sku_id]):
            return http.HttpResponseForbidden('缺少必传参数')
        if len(comment) < 5:
            return http.HttpResponseForbidden('评论长度应大于5')
        try:
            # 查看订单是否评论过
            OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
            sku = SKU.objects.get(id=sku_id)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单错误')
        if is_anonymous:
            # 判断数据是否为布尔类型
            if not isinstance(is_anonymous, bool):
                return http.HttpResponseForbidden('非指定参数')
        # 3.处理业务逻辑

        # 更新商品信息
        OrderGoods.objects.filter(order_id=order_id, sku_id=sku_id).update(comment=comment, score=score,
                                                                           is_anonymous=is_anonymous, is_commented=True)

        # 商品评价+1
        sku.comments += 1
        sku.save()
        # spu商品类型评价+1
        sku.spu.comments += 1
        sku.spu.save()

        # 如果该订单下的所有商品都评价了,修改订单状态为完成
        if OrderGoods.objects.filter(order_id=order_id, is_commented=False).count() == 0:
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['FINISHED'])
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '评价成功'})
