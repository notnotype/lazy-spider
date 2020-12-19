import os
import sys

sys.path.append(os.pardir)

from spider.cache import SqliteCache


class TestSqliteCache:
    def setup_class(self):
        self.cache = SqliteCache()

        # for i in range(100):
        #     self.cache.cache(str(i), {}, 1)

    def test_cache(self):
        assert self.cache.cache('www.baidu.com', {'date': '01001100101'}, alive_time=2)
        assert self.cache.is_cached('www.baidu.com') is True

    def test_is_cached(self):
        assert self.cache.is_cached('asdfsda') is False
        assert self.cache.is_cached('www.baidu.com') is True

    def test_from_cache(self):
        item = self.cache.from_cache('www.baidu.com')
        assert item == {'date': '01001100101'}
        item = self.cache.from_cache('something')
        assert item is None

    def test_clear_more_caches(self):
        self.cache.cache_size = 50
        self.cache.clear_more_caches()


    def test_clear_cache(self):
        self.cache.cache('will del', {}, alive_time=1)
        will_del = self.cache.from_cache('will del')
        assert will_del == {}
        assert self.cache.clear_cache('will del') == 1
        will_del = self.cache.from_cache('will del')
        assert will_del is None

    def test_cache_alive_time(self):
        self.cache.cache('will del', {}, alive_time=-1)
        will_del = self.cache.from_cache('will del')
        assert will_del is None

