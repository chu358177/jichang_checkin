import requests
import json
import os
import traceback
from urllib.parse import quote

session = requests.session()

# 机场地址，例如：https://xxx.com
url = os.environ.get('URL', '').strip().rstrip('/')

# CONFIG 格式：
# 第一行：账号1
# 第二行：密码1
# 第三行：账号2
# 第四行：密码2
config = os.environ.get('CONFIG', '').strip()

# Server 酱 Key，可为空
SCKEY = os.environ.get('SCKEY', '').strip()

#Bark key
BARK_KEY = os.environ.get('BARK_KEY', '').strip()

login_url = f'{url}/auth/login'
check_url = f'{url}/user/checkin'


def push_msg(content):
    if not SCKEY:
        return

    try:
        push_url = (
            f'https://sctapi.ftqq.com/{SCKEY}.send'
            f'?title={quote("机场签到")}&desp={quote(content)}'
        )
        resp = requests.post(url=push_url, timeout=15)
        print('推送状态码:', resp.status_code)
        print('推送返回:', resp.text)
    except Exception as e:
        print('推送失败:', e)

def push_bark(content):
    print("BARK_KEY:",BARK_KEY)
    if not BARK_KEY:
        return
        
    try:
        push_url = (
            f'https://api.day.app/{BARK_KEY}/{quote(content)}'
        )
        resp = requests.get(url=push_url, timeout=15)
        print('Bark推送状态码:', resp.status_code)
        print('Bark推送返回:', resp.text)
    except Exception as e:
        print('Bark推送失败:', e)

def parse_json_response(resp, name):
    print(f'{name}状态码:', resp.status_code)
    print(f'{name}返回:', resp.text)

    try:
        return resp.json()
    except Exception:
        print(f'{name}返回的不是合法 JSON')
        raise


def sign(order, user, pwd):
    header = {
        'origin': url,
        'referer': f'{url}/auth/login',
        'user-agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/109.0.0.0 Safari/537.36'
        )
    }

    data = {
        'email': user,
        'passwd': pwd
    }

    content = ''

    try:
        print(f'===账号{order}进行登录...===')
        print(f'账号：{user}')

        if not url:
            raise Exception('URL 环境变量为空')

        # 登录
        login_resp = session.post(
            url=login_url,
            headers=header,
            data=data,
            timeout=20
        )

        login_result = parse_json_response(login_resp, '登录')

        login_msg = login_result.get('msg', '')
        print('登录消息:', login_msg)

        # 一般机场登录成功会 ret=1
        if login_result.get('ret') not in [1, True, '1']:
            raise Exception(f'登录失败：{login_result}')

        # 签到
        check_resp = session.post(
            url=check_url,
            headers=header,
            timeout=20
        )

        check_result = parse_json_response(check_resp, '签到')

        check_msg = check_result.get('msg', '')
        print('签到消息:', check_msg)

        content = check_msg if check_msg else str(check_result)

        push_msg(content)
        push_bark(content)

    except Exception as e:
        content = f'签到失败：{e}'
        print(content)
        print('错误类型:', type(e))
        traceback.print_exc()

        push_msg(content)
        push_bark(content)

    print(f'===账号{order}签到结束===\n')


if __name__ == '__main__':
    if not config:
        print('CONFIG 环境变量为空')
        exit(1)

    configs = [line.strip() for line in config.splitlines() if line.strip()]

    if len(configs) % 2 != 0:
        print('配置文件格式错误：CONFIG 必须是账号、密码成对出现')
        exit(1)

    user_quantity = len(configs) // 2

    for i in range(user_quantity):
        user = configs[i * 2]
        pwd = configs[i * 2 + 1]
        sign(i, user, pwd)
