__author__ = 'Notnotype'

import logging
import socket
import telnetlib
from random import choice
from typing import Callable, List

import requests
from peewee import *

from lazy_spider import Spider

logger = logging.getLogger('lazy_spider')

HTTP = 1
HTTPS = 2
HTTP_HTTPS = 3
SOCK5 = 4
HTTP_SOCK5 = 5
HTTPS_SOCK5 = 6
HTTP_HTTPS_SOCK5 = 7


class Apis:
    def __init__(self, ip):
        self.ip = ip
        self.api_names = ['api_check_1', 'api_check_2']

    def api_check_1(self, proxies: dict, timeout=(5, 5)):
        try:
            resp = requests.get('https://api.ipify.org/', timeout=timeout, proxies=proxies)
            logger.debug(resp.text)
            if resp.text != self.ip:
                return True
            else:
                return False
        except requests.RequestException:
            return False

    def api_check_2(self, proxies: dict, timeout=(5, 5)):
        try:
            resp = requests.get('http://icanhazip.com/', timeout=timeout, proxies=proxies)
            logger.debug('resp.text: {}, proxies: {}', resp.text, proxies)
            if resp.text != self.ip:
                return True
            else:
                return False
        except requests.RequestException:
            return False


def parse_proxy_url(url: str) -> tuple:
    """解析代理url to `username, password, host, port`
    """
    url = url[url.find('//') + 2:]
    a = url.split('@')
    username = ''
    password = ''
    if len(a) == 2:
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


class GenericProxyChecker:
    # telnet 失败(端口没开)
    CANT_TELNET = 0
    # ip检测失败, 未代理
    CANT_PROXY = 1
    OK = 2

    def __init__(self, apis: Apis):
        self.apis = apis
        self.timeout: tuple = (3, 3)
        self.sock_timeout: int = 3

    def telnet_check(self, ip, port, timeout=None) -> bool:
        # logger.debug('ip: {}, port: {}, timeout: {}', ip, port, timeout)
        if not timeout:
            timeout = self.timeout
        try:
            telnetlib.Telnet(ip, port=port, timeout=timeout)
            return True
        except socket.timeout:
            return False
        except Exception as e:
            logger.debug('ip:{} port:{}', ip, port)
            logger.exception(e)

    def check(self, proxies: dict, timeout=None) -> bool:
        """测试代理是否能够连接"""
        if not timeout:
            timeout = self.sock_timeout
        url: str = list(proxies.items())[0][1]
        username, password, host, port = parse_proxy_url(url)
        if self.telnet_check(host, port, timeout=timeout):
            logger.debug('\033[1;44;44mAPI测试{}\033[0m', proxies)
            if getattr(self.apis, choice(self.apis.api_names))(proxies, timeout):
                return True
            else:
                return False
        else:
            return False

    def proxy_info(self, proxies: dict, timeout=None) -> int:
        """测试代理, 给出详细信息"""
        if not timeout:
            timeout = self.sock_timeout
        url: str = list(proxies.items())[0][1]
        username, password, host, port = parse_proxy_url(url)

        if self.telnet_check(host, port, timeout=timeout):
            if getattr(self.apis, choice(self.apis.api_names))(proxies, timeout):
                return self.OK
            else:
                return self.CANT_PROXY
        else:
            return self.CANT_TELNET

    def set_timeout(self, timeout: tuple):
        self.timeout = timeout

    def set_sock_timeout(self, sock_timeout: int):
        self.sock_timeout = sock_timeout


class ProxyPoolBase:
    def __init__(self):
        ...

    def get_proxies(self, count=1) -> List:
        ...

    def add_proxy(self, host, port, username=None, password=None, schema=HTTP):
        ...

    def del_proxy(self, host, port) -> int:
        ...

    def get_in_middlewares(self) -> List[Callable]:
        ...

    def add_in_middleware(self, middleware: Callable):
        ...

    def get_out_middlewares(self) -> List[Callable]:
        ...

    def add_out_middleware(self, middleware: Callable):
        ...


class SqliteProxy(Model):
    host = CharField()
    port = IntegerField()
    schema = IntegerField()
    username = CharField(null=True)
    password = CharField(null=True)

    # 其他数据
    datetime = DateTimeField(null=True)
    data = CharField(null=True)


def default_in_middleware(model: SqliteProxy, host, port,
                          schema, username, password) -> SqliteProxy:
    model.host = host
    model.port = port
    model.schema = schema
    model.username = username
    model.password = password
    return model


def default_out_middleware(model: SqliteProxy, proxy: dict) -> dict:
    proxy = {}
    schema = model.schema
    _http = schema & 1
    _https = schema & 2
    _sock5 = schema & 4
    if _http:
        proxy['http'] = 'http://{username}{password}{host}:{port}'.format(
            username=model.username + ':' if model.username else '',
            password=model.password + '@' if model.password else '',
            host=model.host,
            port=model.port
        )
    if _https:
        proxy['https'] = 'https://{username}{password}{host}:{port}'.format(
            username=model.username + ':' if model.username else '',
            password=model.password + '@' if model.password else '',
            host=model.host,
            port=model.port
        )
    if _sock5:
        proxy['sock5'] = 'sock5://{username}{password}{host}:{port}'.format(
            username=model.username + ':' if model.username else '',
            password=model.password + '@' if model.password else '',
            host=model.host,
            port=model.port
        )
    return proxy


class SqliteProxyPool(ProxyPoolBase):

    def __init__(self, db: SqliteDatabase):
        super().__init__()
        self.in_middlewares: List[Callable] = [default_in_middleware]
        self.out_middlewares: List[Callable] = [default_out_middleware]
        # init database
        self.db = db
        SqliteProxy._meta.set_database(db)
        if not db.is_connection_usable():
            db.connect()
        if not db.table_exists(SqliteProxy):
            db.create_tables([SqliteProxy])

    def get_proxies(self, count=1) -> List:
        proxies = []
        query = SqliteProxy.select().order_by(self.db.random()).limit(count)
        for model in query:
            proxy = {}
            for middleware in self.out_middlewares:
                proxy = middleware(model, proxy)
            proxies.append(proxy)
        return proxies

    def add_proxy(self, host: str, port: int, schema=HTTP, username=None, password=None):
        query = SqliteProxy.select().where((SqliteProxy.host == host) & (SqliteProxy.port == port))
        if query:
            model = query[0]
        else:
            model = SqliteProxy()
        for middleware in self.in_middlewares:
            model = middleware(model, host, port, schema, username, password)
        model.save()

    def del_proxy(self, host: str, port: int):
        query = SqliteProxy.select().where((SqliteProxy.host == host) & (SqliteProxy.port == port))
        counts = len(query)
        for each in query:
            each.delete_instance()
        return counts

    def get_in_middlewares(self) -> List[Callable]:
        return self.in_middlewares

    def add_in_middleware(self, middleware: Callable):
        self.in_middlewares.append(middleware)

    def get_out_middlewares(self) -> List[Callable]:
        return self.in_middlewares

    def add_out_middleware(self, middleware: Callable):
        self.out_middlewares.append(middleware)


from collections import deque


def generic_item_middleware(collector, item: dict):
    proxy_pool: ProxyPoolBase = collector.proxy_pool
    proxy_pool.add_proxy(item['host'], (item['port']))
    return item


def generic_request_middleware(collector, request: str):
    return requests


class ProxyCollector:
    start_urls = []

    def __init__(self, proxy_pool: ProxyPoolBase, spider=None):
        if not spider:
            spider = Spider()

        self.spider = spider
        self.queue = deque()
        self.items = []
        self.queue += self.start_urls
        self.proxy_pool = proxy_pool

        self.item_middlewares = [generic_item_middleware]
        self.request_middlewares = [generic_request_middleware]

    def process_item(self, item: dict):
        logger.debug('process_item: {}', str(item))
        for each in self.item_middlewares:
            item = each(self, item)
        return item

    def process_request(self, request: str):
        logger.debug('process_request: {}', str(request))
        for each in self.request_middlewares:
            request = each(self, request)
        return request

    def parse(self, response):
        yield None

    def run(self):
        while self.queue:
            url = self.queue.popleft()
            url = self.process_request(url)
            response = self.spider.get(url)
            for each in self.parse(response):
                print(each, type(each))
                if isinstance(each, dict):
                    each = self.process_item(each)
                    self.items.append(each)
                elif isinstance(each, str):
                    self.queue.append(each)
                else:
                    logger.debug('No item yield')
