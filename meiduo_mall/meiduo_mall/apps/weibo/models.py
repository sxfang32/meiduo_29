from django.db import models

from meiduo_mall.utils.models import BaseModel
# Create your models here.s


class OAuthWeiboUser(BaseModel):
    """新郎登录用户数据"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    wb_openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_weibo'
        verbose_name = '新浪微博登录用户数据'
        verbose_name_plural = verbose_name