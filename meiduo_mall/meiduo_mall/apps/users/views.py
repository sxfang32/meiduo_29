import json
import random
from django.contrib.auth import login, authenticate, logout, mixins
from django.core.mail import send_mail
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.views import View
from django import http
from django.conf import settings
import re
from django_redis import get_redis_connection
from itsdangerous import Serializer, BadData

from meiduo_mall.utils.response_code import RETCODE
from verifications.constants import IMAGE_CODE_EXPIRE, SEND_SMS_TIME
from .models import User, Address
from meiduo_mall.utils.views import LoginRequiredView
from celery_tasks.email.tasks import send_verify_email
from celery_tasks.sms.tasks import send_sms_code
from .utils import generate_email_verify_url, check_email_verify_url, generate_access_token, check_access_token
from goods.models import SKU
import logging
from carts.utils import merge_cart_cookie_to_redis

logger = logging.getLogger('django')


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """展示用户注册界面"""
        return render(request, 'register.html')

    def post(self, request):
        """用户注册逻辑"""
        # 接收请求体中的表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        sms_code = query_dict.get('sms_code')
        allow = query_dict.get('allow')
        # 校验数据
        if all([username, password, password2, mobile, allow]) is False:
            return http.HttpResponseForbidden('参数不全，请重新输入')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password2 != password:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')

        # 短信验证码校验
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 将redis中的短信验证码字符串获取出来
        sms_code_server_bytes = redis_conn.get('sms_%s' % mobile)
        # 短信验证码从redis获取出来之后就从Redis数据库中删除:让图形验证码只能用一次
        redis_conn.delete('sms_%s' % mobile)
        # 判断redis中是否获取到短信验证码(判断是否过期)
        if sms_code_server_bytes is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '短信验证码错误'})
        # 从redis获取出来的数据注意数据类型问题byte
        sms_code_server = sms_code_server_bytes.decode()
        # 判断短信验证码是否相等
        if sms_code != sms_code_server:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '短信验证码输入错误'})

        # 使用表单提交，如果勾选了checkbox选项，会自动带上allow : on
        # if allow != 'on':
        #     return HttpResponseForbidden('请勾选用户协议')
        # 新增用户记录
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})

        # 状态保持 JWT
        # 将用户的id值存储到session中，会生成一个session存储到对应用户自己的浏览器cookie中
        login(request, user)

        # 跳转到首页
        response = redirect('/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        return response


class UsernameCountView(View):
    """判断用户名是否重复"""

    def get(self, request, username):
        # 从数据库查询当前username是否重复
        count = User.objects.filter(username=username).count()
        # 响应
        return http.JsonResponse({"count": count})


class MobileCountView(View):
    """判断手机号是否重复"""

    def get(self, request, mobile):
        # 从数据库查询当前username是否重复
        count = User.objects.filter(mobile=mobile).count()
        # 响应
        return http.JsonResponse({"count": count})


class LoginView(View):
    """用户登录"""

    def get(self, request):
        """提供登录的界面"""
        return render(request, 'login.html')

    def post(self, request):
        """登录功能逻辑"""
        # 1.接收请求体表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        # 2.校验
        user = authenticate(request, username=username, password=password)
        # 如果登录失败
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 3.状态保持
        login(request, user)

        # 如果用户没有勾选记住登录
        # 如果session过期时间设置为None，表示使用默认的14天，如果设置为0，代表关闭浏览器失效
        # 如果cookie过期时间设置为None，表示关闭浏览器就过期，如果设置为0，代表直接删除
        if remembered is None:
            request.session.set_expiry(0)  # 是指session的过期时间为关闭浏览器过期
        # 4.重定向

        next = request.GET.get('next')  # 尝试去获取查询参数中是否有用户界面的来源，如果有来源，成功登录后跳转到来源界面
        response = redirect(next or '/')  # 创建响应对象
        # 给cookie设置username
        response.set_cookie('username', user.username,
                            max_age=None if remembered is None else settings.SESSION_COOKIE_AGE)
        # 合并购物车
        merge_cart_cookie_to_redis(request, response)
        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        # 1.清除状态保持
        logout(request)

        # 2.清除cookie中的username
        response = redirect('/login/')
        response.delete_cookie('username')  # 其实delete_cookie本质就是set_cookie(max_age=0)

        # 3.重定向到login界面
        return response


class InfoView(LoginRequiredView):
    """用户中心页面展示"""

    def get(self, request):
        """提供个人信息界面"""
        content = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', content)


class EmailView(LoginRequiredView):
    """添加邮箱功能"""

    def put(self, request):
        """添加邮箱（本质是把空值改掉）"""
        # 接收请求体中的数据
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验数据
        if not email:
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            # return http.JsonResponse({'code': RETCODE.EMAILERR, 'errmsg': '邮箱格式错误'})
            return http.HttpResponseForbidden('邮箱格式不正确')

        # 后期如果需要判断用户的邮箱输入的邮箱是否重复，可以用此判断
        # count = User.objects.filter(email=email).count()
        # if count != 0:
        #     return http.HttpResponseForbidden('邮箱重复')

        # 业务逻辑实现
        # 获取当前登录用户user
        user = request.user

        # 修改email
        user = User.objects.get(username=user.username)
        user.email = email
        user.save()
        # User.objects.filter(username=user.username).update(email=email)
        # user.email = email
        # user.save()

        # 发送邮件
        # send_mail(subject='美多商城', # 邮件主题
        #           message='邮件普通内容', # 邮件普通内容
        #           from_email='美多商城<itcast99@163.com>', # 发件人
        #           recipient_list=[email], # 收件人
        #           html_message="<a href='http://www.itcast.cn''>传智<a>")  # 超文本内容
        # verify_url = 'http://www.meiduo.site:8000/verify_email?token='

        verify_url = generate_email_verify_url(user)
        send_verify_email.delay(email, verify_url)
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


class VerifyEmailView(View):
    """激活邮箱"""

    def get(self, request):
        # 1.接收查询参数中的token
        token = request.GET.get('token')
        # 2.校验token
        if token is None:
            return http.HttpResponseForbidden('缺少token')

        # 3.修改当前user的email_active为1
        user = check_email_verify_url(token)
        if user is None:
            return http.HttpResponseForbidden('token无效')
        user.email_active = True
        user.save()
        # 4.重定向到用户中心
        return render(request, 'user_center_info.html')


class AdressesView(LoginRequiredView):
    """用户收货地址"""

    def get(self, request):
        """展示用户收货地址"""

        user = request.user

        # 1.查询当前登录用户所有未被逻辑删除的收货地址
        address_qs = Address.objects.filter(user=user, is_deleted=False)
        # address_qs = user.addresses.filter(is_delete=False)
        # 遍历查询集中每个address模型，转化成字典，并包装到列表中
        addresses = []
        for address in address_qs:
            addresses.append(
                {
                    "id": address.id,
                    "title": address.title,
                    "receiver": address.receiver,
                    "province_id": address.province_id,
                    "province": address.province.name,
                    "city_id": address.city_id,
                    "city": address.city.name,
                    "district_id": address.district_id,
                    "district": address.district.name,
                    "place": address.place,
                    "mobile": address.mobile,
                    "tel": address.tel,
                    "email": address.email
                }
            )

        context = {
            'addresses': addresses,
            'default_address_id': user.default_address_id  # 获取当前用户的默认收货地址ID
        }
        return render(request, 'user_center_site.html', context)


class CreateAddressView(LoginRequiredView):
    """新增收货地址"""

    def post(self, request):

        # 查询当前用户收货地址数量
        count = Address.objects.filter(user=request.user, is_deleted=False).count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '收货地址超过上限'})

        # 接收请求体的非表单body
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title'),
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 创建Address模型对象 并save
        try:
            address = Address.objects.create(
                user=request.user,
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except DatabaseError as e:
            logger.error(e)
            return http.HttpResponseForbidden('收货地址数据有误')

        # 设置一个默认地址，判断如果没有默认地址，新增的这个就是默认地址
        if request.user.default_address is None:
            request.user.default_address = address
            request.user.default_address.save()

        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        # 将新增的收货地址模型对象转换成字典响应给前端
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province_id": address.province_id,
            "province": address.province.name,
            "city_id": address.city_id,
            "city": address.city.name,
            "district_id": address.district_id,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '新增收货地址成功', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""

        # 校验要修改的收货地址是否存在
        try:
            address = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id不存在')

        # 接收请求体的非表单body
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title'),
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 给Address模型对象并save
        try:
            # Address.objects.filter(id=address_id).update(
            #     title=title,
            #     receiver=receiver,
            #     province_id=province_id,
            #     city_id=city_id,
            #     district_id=district_id,
            #     place=place,
            #     mobile=mobile,
            #     tel=tel,
            #     email=email
            # )
            # 更加合理的写法
            address = Address.objects.get(id=address_id)
            address.title = title
            address.receiver = receiver
            address.province_id = province_id
            address.city_id = city_id
            address.district_id = district_id
            address.place = place
            address.mobile = mobile
            address.tel = tel
            address.email = email
            address.save()
        except DatabaseError as e:
            logger.error(e)
            return http.HttpResponseForbidden('收货地址数据有误')

        # 重新从数据库查询新的收货地址
        # address = Address.objects.get(id=address_id)

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province_id": address.province_id,
            "province": address.province.name,
            "city_id": address.city_id,
            "city": address.city.name,
            "district_id": address.district_id,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改收货地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """删除指定收货地址"""
        # 校验
        try:
            address = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})
        # 修改
        address.is_deleted = True
        address.save()

        # TODO 需要加一个判断，如果删除的是默认地址，需要重新将用户的默认地址置为None

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class DefaultAddressView(LoginRequiredView):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""

        # 校验要设置的地址是否存在
        try:
            address = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})
        # 获取当前user
        user = request.user
        user.default_address = address
        user.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(LoginRequiredView):
    """修改标题"""

    def put(self, request, address_id):
        """修改标题"""
        try:
            address = Address.objects.get(id=address_id, user=request.user, is_deleted=False)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '修改地址标题失败'})

        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        if title is None:
            return http.HttpResponseForbidden('缺少必传参数')
        address.title = title
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改标题成功'})


class ChangePasswordView(LoginRequiredView):
    """修改用户密码"""

    def get(self, request):
        """展示修改密码页面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """修改密码逻辑"""

        # 接收表单数据
        query_dict = request.POST
        old_pwd = query_dict.get('old_pwd')
        new_pwd = query_dict.get('new_pwd')
        new_cpwd = query_dict.get('new_cpwd')

        # 校验数据
        if all([old_pwd, new_pwd, new_cpwd]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        user = request.user
        if user.check_password(old_pwd) is False:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 修改当前登录用户的set_password
        user.set_password(new_pwd)
        user.save()

        # 让用户重新登录
        logout(request)
        response = redirect('/login/')
        response.delete_cookie('username')
        return response


class UserBrowseHistory(View):
    """保存用户商品浏览记录"""

    def post(self, request):
        """保存浏览记录"""
        user = request.user
        if not user.is_authenticated:
            # 如果用户未登录，提前响应
            return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})

        # 1.接收用户参数sku_id
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 2.校验数据
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')

        # 3.创建redis连接对象
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = user.id

        key = 'history_%s' % user_id
        # 3.1去重
        pl.lrem(key, 0, sku_id)
        # 3.2存储数据,添加到列表开头
        pl.lpush(key, sku_id)
        # 3.3截取数据
        pl.ltrim(key, 0, 4)
        # 3.4执行管道
        pl.execute()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        """展现用户浏览记录"""

        user = request.user
        if not user.is_authenticated:
            # 如果用户未登录，提前响应
            return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})

        # 获取Redis存储的sku_id列表信息
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)

        # 根据sku_ids列表数据，查询出商品sku信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            # 将sku模型转成字典
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


class FindPasswordView(View):
    """展示找回密码界面"""

    def get(self, request):
        return render(request, 'find_password.html')


class CheckUserView(View):
    """找回密码输入账户"""

    def get(self, request, username):
        query_dict = request.GET
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return http.JsonResponse({'error': '用户名或手机号不存在'}, status=404)
        verify_codes = query_dict.get('text')
        uuid = query_dict.get('image_code_id')

        mobile = user.mobile

        if all([username, verify_codes]) is False:
            return http.HttpResponseForbidden('参数不全')

        # # 判断用户名是否存在
        # count_username = User.objects.filter(username=username)
        # if not count_username:
        #     return http.JsonResponse({'status': 404})

        # 判断验证码是否正确
        if all([verify_codes, uuid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        # 创建redis连接
        redis_conn = get_redis_connection('verify_codes')
        # 将redis中的图形验证码字符串获取出来.这是一个字节类型的数据
        image_code_server_bytes = redis_conn.get(uuid)
        # 图形验证码从redis获取出来之后就从Redis数据库中删除:让图形验证码只能用一次
        redis_conn.delete(uuid)
        # 判断redis中是否获取到图形验证码(判断是否过期)
        if image_code_server_bytes is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码错误'})
        # 从redis获取出来的数据注意数据类型问题byte，先进行decode操作
        image_code_server = image_code_server_bytes.decode()
        # 判断时要注意字典大小写问题
        if verify_codes.lower() != image_code_server.lower():
            return http.JsonResponse({'error': '验证码错误'}, status=400)

        # 加密一个access_token
        access_token = generate_access_token(user)

        response = http.JsonResponse({'message': 'ok', 'mobile': mobile, 'access_token': access_token})
        response.set_cookie('mobile', mobile, max_age=3600)
        return response


class SMSMobileView(View):
    """发送手机短信验证码"""

    def get(self, request):
        query_dict = request.GET
        access_token = query_dict.get('access_token')
        mobile = request.COOKIES.get('mobile')

        # 对access_token解密

        ver_token = check_access_token(access_token)

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            return http.JsonResponse({'error': '用户名或手机号不存在'}, status=404)

        if user == ver_token:
            sms_code = '%06d' % random.randint(0, 999999)
            print(sms_code)
            # 创建Redis管道
            redis_conn = get_redis_connection('verify_codes')
            pl = redis_conn.pipeline()
            # 将短信验证码存储到redis，key为了保持唯一，统一sms_手机号格式
            # redis_conn.setex('sms_%s' % mobile, IMAGE_CODE_EXPIRE, sms_code)
            pl.setex('sms_%s' % mobile, IMAGE_CODE_EXPIRE, sms_code)

            # 当手机号发过了验证码，向Redis存储一个发送过的标记
            # 可能存在没存进去的问题，这时候可以使用ttl获取一下那个300秒的验证码，时间够不够300-60秒
            pl.setex('send_flag_%s' % mobile, SEND_SMS_TIME, 1)

            # 执行管道
            pl.execute()

            # 利用容联云平台进行发送短信
            send_sms_code.delay(mobile, sms_code)  # 将发短信的函数内存添加到仓库中，让worker去新的线程执行

            # 响应
            return http.JsonResponse({'message': 'OK'})


class CheckSMSView(View):
    """校验短信验证码"""

    def get(self, request, username):
        query_dict = request.GET
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return http.HttpResponseForbidden('用户名不存在')
        sms_code = query_dict.get('sms_code')
        mobile = request.COOKIES.get('mobile')

        redis_conn = get_redis_connection('verify_codes')

        sms_code_server_bytes = redis_conn.get('sms_%s' % mobile)
        # 短信验证码从redis获取出来之后就从Redis数据库中删除:让图形验证码只能用一次
        redis_conn.delete('sms_%s' % mobile)
        # 判断redis中是否获取到短信验证码(判断是否过期)
        if sms_code_server_bytes is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '短信验证码错误'})
        # 从redis获取出来的数据注意数据类型问题byte
        sms_code_server = sms_code_server_bytes.decode()
        # 判断短信验证码是否相等
        if sms_code != sms_code_server:
            return http.JsonResponse({'error': '验证码错误'}, status=400)

        # 封装access_token
        access_token = generate_access_token(user)

        resopnse = http.JsonResponse({'user_id': user.id, 'access_token': access_token})
        resopnse.set_cookie('mobile', mobile)
        return resopnse


class ResetPasswordView(View):
    """重置密码"""

    def post(self, request, user_id):
        json_dict = json.loads(request.body.decode())
        access_token = json_dict.get('access_token')
        ver_token = check_access_token(access_token)
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return http.JsonResponse({'error': '用户错误'}, status=400)

        if all([password, password2]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.JsonResponse({'error': '密码最少8位，最长20位'}, status=400)

        if password2 != password:
            return http.JsonResponse({'error': '两次密码不一致'}, status=400)

        if ver_token != user:
            return http.JsonResponse({'error': '用户数据错误'}, status=400)

        else:
            user.set_password(password)
            user.save()

            return http.JsonResponse({'message': 'ok'})
