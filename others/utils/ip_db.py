import telnetlib
from random import choice

import requests


class Apis:
    def __init__(self):
        self.timeout = (3, 3)
        self.api_names = ['api_check_1', 'api_check_2']

    def api_check_1(self, proxies: dict):
        try:
            resp = requests.get('https://api.ipify.org/', timeout=self.timeout, proxies=proxies)
            if resp.content.decode() == list(proxies.values())[0]:
                return True
            else:
                return False
        except requests.RequestException:
            return False

    def api_check_2(self, proxies):
        try:
            resp = requests.get('http://icanhazip.com/', timeout=self.timeout, proxies=proxies)
            if resp.content.decode() == list(proxies.values())[0]:
                return True
            else:
                return False
        except requests.RequestException:
            return False


def parse_proxy_url(url: str):
    url = url[url.find('//') + 2:]
    a = url.split('@')
    username = ''
    password = ''
    if a == 2:
        has_auth = True
    else:
        has_auth = False

    if has_auth:
        username, password = a[0].split(':')
        password = int(password)
        host, port, = a[1].split(':')
        port = int(port)
    else:
        host, port, = a[0].split(':')
        port = int(port)

    return username, password, host, port


def test_parse_proxy_url():
    url1 = 'http://175.42.128.241:9999'
    url2 = 'http://175.42.128.241:9999'
    username, password, host, port = parse_proxy_url(url1)
    print(username, password, host, port)
    username, password, host, port = parse_proxy_url(url2)
    print(username, password, host, port)


class ProxyChecker:
    def __init__(self, apis: Apis):
        self.apis = apis
        self.timeout: tuple = (3, 3)

    def telnet_check(self, host: str, port: int, timeout=None):
        if not timeout:
            timeout = self.timeout
        try:
            telnetlib.Telnet(host, port=port, timeout=timeout)
            return True
        except Exception as e:
            print('type : ', type(e))
            return False

    def check_one(self, proxies: dict, timeout=None):
        if not timeout:
            timeout = self.timeout
        url: str = list(proxies.items())[0][1]
        username, password, host, port = parse_proxy_url(url)
        if self.telnet_check(host, port, timeout=timeout):
            if getattr(self.apis, choice(self.apis.api_names))(proxies, timeout):
                return True
            else:
                return False
        else:
            return False

    def set_timeout(self, timeout: tuple):
        self.timeout = timeout
