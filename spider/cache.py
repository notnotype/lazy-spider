import datetime
import json
import logging
import os
import pickle
import uuid
from json import load, dump
from os.path import exists
from os.path import join
from typing import Union

from peewee import *

from .utils import limit_text

logger = logging.getLogger('spider')
db = SqliteDatabase('sqlite.db')


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
        # todo 缓存最大容量, 超出自动删除最旧的缓存
        # todo 改用 `sqlite` 存 `json`
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

    def clear_all(self):
        self.__cache_json = {"cached_files": {}}


class SqliteCacheData(Model):
    url = CharField()
    typing = CharField()
    alive_time = DateField()
    data = TextField()

    class Meta:
        database = db


class SqliteCache(CacheBase):

    def __init__(self):
        super().__init__()
        if not db.is_connection_usable():
            db.connect()
        if not db.table_exists(SqliteCacheData):
            db.create_tables([SqliteCacheData])

    def is_cached(self, name: str, ignore_date=False) -> bool:
        query = SqliteCacheData.select().where(SqliteCacheData.url == name)
        if query:
            item = query[0]
            alive_time = item.alive_time
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
            item = SqliteCacheData.select().where(SqliteCacheData.url == name)
            return pickle.loads(item.data)
        else:
            return None

    def cache(self, name: str, obj, alive_time: Union[datetime.datetime, int]) -> bool:
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
        logger.debug('缓存: {} -> {}'.format(limit_text(name, 200), str(db)))
        return True

    def save(self):
        super().save()

    def clear_all(self):
        super().clear_all()


...
