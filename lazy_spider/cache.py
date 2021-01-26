import datetime
import json
import logging
import os
import pickle
import uuid
from json import load, dump
from math import ceil
from os.path import exists
from os.path import join
from typing import Union

from peewee import *

from .utils import limit_text, get_sqlite_db

logger = logging.getLogger('lazy_spider')
db = get_sqlite_db()


class CacheBase:
    def __init__(self):
        self.cache_size = 10000
        # "filename": str(uuid.uuid4()),
        # "typing": str(obj.__class__),
        # "alive_time": alive_time.strftime('%Y-%m-%d %H:%M:%S')

    def is_cached(self, name: str, ignore_date=False) -> bool:
        ...

    def from_cache(self, name: str, force=False) -> object:
        ...

    def cache(self, name: str, obj, alive_time: Union[datetime.datetime, int]) -> bool:
        ...

    def save(self):
        ...

    def clear_cache(self, name: str):
        ...

    def clear_all(self):
        ...


class JsonCache(CacheBase):
    """
    __init__
    cache
    from_cache
    is_cached
    close
    """

    def __init__(self, cache_dir='__pycache__'):
        super().__init__()
        self.__cache_dir = cache_dir
        self.__cache_json_name = 'cache.json'
        self.cache_size = 10000
        if not exists(cache_dir):
            os.makedirs(cache_dir)
            logger.debug('生成文件缓存路径{}', os.path.realpath(cache_dir))
        # 是否存在`cache.json`,没有则生成
        if not exists(join(cache_dir, self.__cache_json_name)):
            try:
                with open(join(self.__cache_dir, self.__cache_json_name), 'a+', encoding='utf8') as f:
                    dump({"cached_files": {}}, f, indent=4, ensure_ascii=False)
            except IOError as e:
                logger.error('IO错误{}', join(self.__cache_dir, self.__cache_json_name))
                raise e
        # 打开缓存清单文件
        try:
            with open(join(cache_dir, self.__cache_json_name), 'r', encoding='utf8') as f:
                self.__cache_json: dict = load(f)
        except IOError as e:
            logger.exception(e)
            logger.error('IO错误{}', join(cache_dir, self.__cache_json_name))
            raise e
        except json.JSONDecodeError as e:
            logger.error('Json解码错误{}', join(cache_dir, self.__cache_json_name))
            raise e
        except Exception as e:
            logger.error('未知错误在{}', join(cache_dir, self.__cache_json_name))
            raise e

    def is_cached(self, name: str, ignore_date=False) -> bool:
        if name in self.__cache_json['cached_files'].keys():
            item = self.__cache_json['cached_files'][name]
            alive_time: datetime.datetime = datetime.datetime.strptime(item['alive_time'], '%Y-%m-%d %H:%M:%S')
            if alive_time > datetime.datetime.now() or ignore_date:
                return True
            else:
                logger.debug('存活时间已过,重新缓存')
                return False
        else:
            return False

    def from_cache(self, name: str, force=False) -> object:
        """

        :param name:
        :param force: 忽略时间过期, 强制从缓存读取
        :return:
        """
        if self.is_cached(name, ignore_date=force):
            item = self.__cache_json['cached_files'][name]
            filename = item['filename']
            with open(join(self.__cache_dir, filename), 'rb') as f:
                return pickle.load(f)
        else:
            return None

    def cache(self, name: str, obj, alive_time: Union[datetime.datetime, int]) -> bool:
        if isinstance(alive_time, int):
            alive_time = datetime.datetime.now() + datetime.timedelta(days=alive_time)
        self.__cache_json['cached_files'][name] = {
            "filename": str(uuid.uuid4()),
            "typing": str(obj.__class__),
            "alive_time": alive_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        item = self.__cache_json['cached_files'][name]
        filename = item['filename']
        try:
            with open(join(self.__cache_dir, filename), 'wb') as f:
                pickle.dump(obj, f)
                self.save()
        except IOError:
            logger.error('IO错误: {}'.format(filename))
            return False
        else:
            logger.debug('缓存: {} -> {}'.format(limit_text(name, 200), filename))
            return True

    # 关闭保存文件
    def save(self):
        try:
            with open(join(self.__cache_dir, self.__cache_json_name), 'r+', encoding='utf8') as f:
                dump(self.__cache_json, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logger.error('IO错误: {}', join(self.__cache_dir, self.__cache_json_name))
            raise e

    def clear_cache(self, name: str):
        if name in self.__cache_json['cached_files']:
            item = self.__cache_json['cached_files'][name]
            filename = item['filename']
            os.remove(join(self.__cache_dir, filename))
            del self.__cache_json['cached_files'][name]
            logger.debug('删除缓存[{}]'.format(name))

    def clear_all(self):
        logger.debug('删除缓存[{}]个'.format(len(self.__cache_json)))
        self.__cache_json = {"cached_files": {}}

    def __repr__(self):
        return self.__cache_json_name


class SqliteCacheData(Model):
    url = CharField()
    typing = CharField()
    alive_time = DateTimeField()
    data = BitField()

    class Meta:
        database = db
        table_name = 'lazy_spider_cache'


class SqliteCache(CacheBase):

    def __init__(self):
        super().__init__()
        if not db.is_connection_usable():
            db.connect()
        if not db.table_exists(SqliteCacheData):
            db.create_tables([SqliteCacheData])
        self.table_name = str(SqliteCacheData)
        self.cache_size = 10000
        self.remain_percent = 0.75

    def is_cached(self, name: str, ignore_date=False) -> bool:
        query = SqliteCacheData.select().where(SqliteCacheData.url == name)
        if query:
            item = query[0]
            alive_time: datetime.date = item.alive_time
            if alive_time > datetime.datetime.now() or ignore_date:
                return True
            else:
                logger.debug('存活时间已过,重新缓存')
                self.clear_cache(name)
                return False
        else:
            return False

    def from_cache(self, name: str, force=False) -> object:
        """

        :param name:
        :param force: 忽略时间过期, 强制从缓存读取
        :return:
        """
        if self.is_cached(name, ignore_date=force):
            item = SqliteCacheData.select().where(SqliteCacheData.url == name)[0]
            return pickle.loads(item.data)
        else:
            return None

    def cache(self, name: str, obj, alive_time: Union[datetime.datetime, int]) -> bool:
        # 清除过多的缓存
        self.clear_more_caches()
        if isinstance(alive_time, int):
            alive_time = datetime.datetime.now() + datetime.timedelta(days=alive_time)
        query = SqliteCacheData.select().where(SqliteCacheData.url == name)
        # 查询
        if not query:
            item = SqliteCacheData()
        else:
            item = query[0]
        # 填充数据
        item.url = name
        item.typing = str(obj.__class__)
        item.alive_time = alive_time.strftime('%Y-%m-%d %H:%M:%S')
        item.data = pickle.dumps(obj)
        logger.debug('缓存: {} -> {}'.format(limit_text(name, 200),
                                           str(SqliteCacheData)))
        return item.save()

    def save(self):
        super().save()

    def clear_more_caches(self):
        if SqliteCacheData.select().count() > self.cache_size:
            logger.debug('删除缓存中......')
            will_del = SqliteCacheData.select() \
                .limit(ceil(self.remain_percent * self.cache_size)) \
                .order_by(SqliteCacheData.alive_time)
            # print('will_del len', will_del.count())
            # del_count: ModelObjectCursorWrapper = will_del.execute()
            for each in will_del:
                each.delete_instance()
            logger.info('缓存过多, 最大缓存大小[{}], 删除缓存[{}]个, 剩下缓存[{}]个'.format(
                self.cache_size,
                will_del.__len__(),
                SqliteCacheData.select().count()
            ))

    def clear_cache(self, name: str):
        result = SqliteCacheData.delete().where(SqliteCacheData.url == name).execute()
        if result:
            logger.debug('删除缓存[{}]'.format(name))
        return result

    def clear_all(self):
        sql = SqliteCacheData.delete()
        result = sql.execute()
        logger.debug('删除缓存[{}]个'.format(result))
        return

    def __repr__(self):
        return self.table_name


class NoCache(CacheBase):
    def __init__(self):
        super().__init__()

    def is_cached(self, name: str, ignore_date=False) -> bool:
        return False

    def from_cache(self, name: str, force=False) -> object:
        return None

    def cache(self, name: str, obj, alive_time: Union[datetime.datetime, int]) -> bool:
        return False

    def save(self):
        super().save()

    def clear_cache(self, name: str):
        super().clear_cache(name)

    def clear_all(self):
        super().clear_all()

    def __repr__(self):
        return 'NoCache'
