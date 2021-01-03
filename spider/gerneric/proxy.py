__author__ = 'Notnotype'

from typing import Callable, List

from peewee import *

HTTP = 1
HTTPS = 2
HTTP_HTTPS = 3
SOCK5 = 4
HTTP_SOCK5 = 5
HTTPS_SOCK5 = 6
HTTP_HTTPS_SOCK5 = 7


class ProxyPoolBase:
    def __init__(self):
        ...

    def get_proxies(self, count=1) -> List:
        ...

    def set_proxy(self, host, port, username=None, password=None, schema=HTTP):
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

    def set_proxy(self, host, port, schema=HTTP, username=None, password=None):
        query = SqliteProxy.select().where(SqliteProxy.host == host and SqliteProxy.port == port)
        if query:
            model = query[0]
        else:
            model = SqliteProxy()
        for middleware in self.in_middlewares:
            model = middleware(model, host, port, schema, username, password)
        model.save()

    def del_proxy(self, host, port):
        sql = SqliteProxy.delete().where(SqliteProxy.host == host and SqliteProxy.port == port)
        return sql.execute()

    def get_in_middlewares(self) -> List[Callable]:
        return self.in_middlewares

    def add_in_middleware(self, middleware: Callable):
        self.in_middlewares.append(middleware)

    def get_out_middlewares(self) -> List[Callable]:
        return self.in_middlewares

    def add_out_middleware(self, middleware: Callable):
        self.out_middlewares.append(middleware)
