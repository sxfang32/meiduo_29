import time
from django.conf import settings
from redis import StrictRedis
import logging

from orders.models import OrderInfo
from celery_tasks.main import celery_app

logger = logging.getLogger("django")

# 连接redis数据库
redis = StrictRedis(host='192.168.27.128', port=6379, decode_responses=True)

# 创建pubsub对象，该对象订阅一个频道并侦听新消息：
pubsub = redis.pubsub()


# 定义触发事件
def event_handler(msg):
    print('Handler', msg)
    print(msg['data'])
    order_id = str(msg['data'])

    # 获取订单对象
    order = OrderInfo.objects.get(order_id=order_id)

    # 判断用户是否已经付款
    if str(order.status) == "1":

        # 取消订单,更改订单状态
        OrderInfo.objects.filter(order_id=order_id).update(status="6")

        # 获取订单中的所有商品
        goods = order.skus.all()

        # 遍历商品
        for good in goods:
            # 获取订单中的商品数量
            count = good.count
            print(count)

            # 获取sku商品
            sku = good.sku

            # 将库存重新增加到sku的stock中去
            sku.stock += count

            # 从销量中减去已经取消的数量
            sku.sales -= count
            sku.save()


# 订阅redis键空间通知
pubsub.psubscribe(**{'__keyevent@5__:expired': event_handler})

# 接收订阅的通知，不需要死循环，否则项目无法启动
while True:
    message = pubsub.get_message()
    if message:
        print(message)
    else:
        time.sleep(0.01)
