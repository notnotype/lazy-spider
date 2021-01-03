__author__ = 'Notnotype'

import logging
from typing import Callable, List

from peewee import *

from spider import Spider

logger = logging.getLogger('spider')

HTTP = 1
HTTPS = 2
HTTP_HTTPS = 3
SOCK5 = 4
HTTP_SOCK5 = 5
HTTPS_SOCK5 = 6
HTTP_HTTPS_SOCK5 = 7


class ProxyCheckerBase:
    def check(self, host, port, username=None, password=None, schema=HTTP, timeout=5) -> bool:
        ...


class GenericProxyChecker(ProxyCheckerBase):
    def check(self, host, port, username=None, password=None, schema=HTTP, timeout=5) -> bool:
        return super().check(host, port, username, password, schema, timeout)


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
        print('*******************************Ok')
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

    def add_proxy(self, host, port, schema=HTTP, username=None, password=None):
        query = SqliteProxy.select().where(SqliteProxy.host == host & SqliteProxy.port == port)
        if query:
            model = query[0]
        else:
            model = SqliteProxy()
        for middleware in self.in_middlewares:
            model = middleware(model, host, port, schema, username, password)
        model.save()

    def del_proxy(self, host, port):
        sql = SqliteProxy.delete().where(SqliteProxy.host == host & SqliteProxy.port == port)
        return sql.execute()

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


def generic_request_middleware(collector, requests: str):
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
