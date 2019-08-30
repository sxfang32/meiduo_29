from rest_framework_jwt.utils import jwt_response_payload_handler


# 自定义，响应数据的构造函数

def jwt_response_cutom_handler(token, user=None, request=None):
    return {
        "token": token,
        "username": user.username,
        "user_id": user.id
    }
