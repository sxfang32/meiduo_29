from fabfile.api import env, run
from fabfile.operations import sudo

GIT_REPO = "git@github.com:sxfang32/meiduo_29.git"

env.user = 'python'
env.password = '123456!'

# 填写你自己的主机对应的域名
env.hosts = ['192.168.27.128']

# 一般情况下为 22 端口，如果非 22 端口请查看你的主机服务提供商提供的信息
env.port = '22'


def deploy():
    source_folder = '/home/ubuntu/site/meiduo_mall'

    run('cd %s && git pull' % source_folder)
    run("""
        cd {} &&
        ../env/bin/pip install -r requirements.txt &&
        ../env/bin/python3 manage.py collectstatic --noinput &&
        ../env/bin/python3 manage.py migrate
        """.format(source_folder))
    sudo('systemctl restart meiduo.service')
    sudo('service nginx reload')
