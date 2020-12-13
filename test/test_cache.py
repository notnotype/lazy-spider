import os
import sys

sys.path.append(os.pardir)

from spider.cache import SqliteCache


class TestSqliteCache:
    def setup_class(self):
        self.cache = SqliteCache()

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

    def test_save(self):
        assert False

    def test_clear_all(self):
        assert False
