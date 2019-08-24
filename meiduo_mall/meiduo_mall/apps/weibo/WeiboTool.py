import json
import urllib
from urllib.parse import urlencode
import requests
from urllib.parse import urlencode, parse_qs

class OAuthWeibo(object):
    """
    微博认证辅助工具类
    """

    def __init__(self, client_id=None, client_key=None, redirect_uri=None, state=None):
        self.client_id = client_id
        self.client_key = client_key
        self.redirect_uri = redirect_uri
        self.state = state   # 用于保存登录成功后的跳转页面路径

    def _post(self, url, data):  # post方法
        request = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(encoding='UTF8'))  # 1
        response = urllib.request.urlopen(request)
        return response.read()

    def get_weibo_url(self):
        # weibo登录url参数组建
        data_dict = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'forcelogin':'true',
        }



        # 构建url
        weibo_url = 'https://api.weibo.com/oauth2/authorize?' + urlencode(data_dict)

        return weibo_url

    # 获取access_token值

    def get_access_token(self, code):
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_key,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        response = self._post('https://api.weibo.com/oauth2/access_token', params)
        result = json.loads(response.decode('utf-8'))
        self.access_token = result["access_token"]
        # self.openid = result["uid"]
        return self.access_token

