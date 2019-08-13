send_mail(subject='美多商城', # 邮件主题
                  message='邮件普通内容', # 邮件普通内容
                  from_email='美多商城<itcast99@163.com>', # 发件人
                  recipient_list=[email],
                  html_message="<a href='http://www.itcast.cn''>传智<a>")