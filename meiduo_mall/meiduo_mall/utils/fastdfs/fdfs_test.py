from fdfs_client.client import Fdfs_client


# 1.创建fdfs客户端实例对象
fdfs_client = Fdfs_client('client.conf')

# 2.上传"本地"文件
ret = fdfs_client.upload_by_filename('/Users/apple/Desktop/bd_logo1.png')

# 上产文件，传入的参数是"文件数据"
# fdfs_client.upload_by_buffer()
print(ret)
