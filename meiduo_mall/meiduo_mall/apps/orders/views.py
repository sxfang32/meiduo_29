import json
from django import http
from django.shortcuts import render
from django_redis import get_redis_connection
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
import logging

from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address
from goods.models import SKU
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

        # 生成订单编号：20190820145030+ user_id
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

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

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order_id})


class OrderSuccessView(LoginRequiredView):
    """提交成功页面"""
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

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }

        return render(request, 'order_success.html', context)
