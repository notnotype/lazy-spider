import os
import sys

sys.path.append(os.pardir)

from lazy_spider.generic import proxy


class TestSqliteProxy:
    def setup(self):
        print('=======setup===========')
        self.pool = SqliteProxyPool(get_sqlite_db())

    def test_in(self):
        pool = self.pool
        pool.add_proxy('127.0.0.1', 80, proxy.HTTP)

    def test_in_https(self):
        pool = self.pool
        pool.add_proxy('127.0.0.2', 80, proxy.HTTP | proxy.HTTPS)
        pool.add_proxy('127.0.0.2', 81, proxy.HTTP | proxy.HTTPS)
        pool.add_proxy('127.0.0.2', 82, proxy.HTTP | proxy.HTTPS)
        pool.add_proxy('127.0.0.2', 83, proxy.HTTP | proxy.HTTPS)

    def test_in_sock5(self):
        pool = self.pool
        pool.add_proxy('127.0.0.3', 80, proxy.HTTP | proxy.SOCK5)

    def test_in_other(self):
        pool = self.pool
        pool.add_proxy('127.0.0.sd', 88, proxy.HTTP | proxy.HTTPS | proxy.SOCK5, username='lhl', password='12')
        pool.add_proxy('1', 777)
        pool.add_proxy('2', 777)
        pool.add_proxy('3', 777)

    def test_out(self):
        pool = self.pool
        proxies = pool.get_proxies(3)
        print()
        for each in proxies:
            print(each)

    def test_del(self):
        pool = self.pool
        pool.add_proxy('127.0.0.3', 80)
        r = pool.del_proxy('127.0.0.3', 80)
        assert r == 1


from lazy_spider.generic.proxy import *


class TestCollection(ProxyCollector):
    start_urls = ['https://www.kuaidaili.com/free/inha/1/']

    def parse(self, response):
        trs = response.xpath("//tbody/tr")
        for tr in trs:
            tds = tr.xpath('.//td')
            host = tds[0].text
            port = tds[1].text
            yield {'host': host, 'port': port}
        url: str = response.url
        a = url.find('inha') + 5
        b = url[a:].replace('/', '')
        page_num = int(b)
        yield f'https://www.kuaidaili.com/free/inha/{page_num + 1}/'


from lazy_spider.utils import get_sqlite_db, sleep


def try_test_collection():
    spider = Spider()
    spider.set_sleeper(lambda: sleep(5))
    tc = TestCollection(SqliteProxyPool(get_sqlite_db()), spider)
    tc.run()
    print(tc.items)


def test_proxy_checker():
    checker = GenericProxyChecker(Apis())
    checker.set_sock_timeout(2)
    pool = SqliteProxyPool(get_sqlite_db())
    for i in range(10):
        _proxy = pool.get_proxies()[0]
        print('check:', _proxy)
        r = checker.check(_proxy)
        print('r =', r)


def main():
    try_test_collection()
    pass


if __name__ == '__main__':
    exit(main())
