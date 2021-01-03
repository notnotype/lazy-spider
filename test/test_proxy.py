from spider.gerneric import SqliteProxyPool, proxy
from spider.utils import get_sqlite_db


class TestSqliteProxy:
    def setup(self):
        print('=======setup===========')
        self.pool = SqliteProxyPool(get_sqlite_db())

    def test_in(self):
        pool = self.pool
        pool.set_proxy('127.0.0.1', 80, proxy.HTTP)

    def test_in_https(self):
        pool = self.pool
        pool.set_proxy('127.0.0.2', 80, proxy.HTTP | proxy.HTTPS)
        pool.set_proxy('127.0.0.2', 81, proxy.HTTP | proxy.HTTPS)
        pool.set_proxy('127.0.0.2', 82, proxy.HTTP | proxy.HTTPS)
        pool.set_proxy('127.0.0.2', 83, proxy.HTTP | proxy.HTTPS)

    def test_in_sock5(self):
        pool = self.pool
        pool.set_proxy('127.0.0.3', 80, proxy.HTTP | proxy.SOCK5)

    def test_in_other(self):
        pool = self.pool
        pool.set_proxy('127.0.0.sd', 88, proxy.HTTP | proxy.HTTPS | proxy.SOCK5, username='lhl', password='12')

    def test_out(self):
        pool = self.pool
        proxies = pool.get_proxies(3)
        print()
        for each in proxies:
            print(each)

    def test_del(self):
        pool = self.pool
        r = pool.del_proxy('127.0.0.3', 80)
        assert r == 1
