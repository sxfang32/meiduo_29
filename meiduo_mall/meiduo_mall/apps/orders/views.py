from django.shortcuts import render
from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address
from goods.models import SKU
from django_redis import get_redis_connection
from decimal import Decimal


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

        freight = Decimal('10.00')  # 运费

        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight
        }
        return render(request, 'place_order.html', context)
