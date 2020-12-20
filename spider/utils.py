import logging
import random
from time import sleep
from typing import Iterable

from fake_useragent import UserAgent
from peewee import SqliteDatabase
from requests import Request

logger = logging.getLogger('spider')


def general_request_pipeline(spider, response) -> Request:
    ...


def general_response_pipeline(spider, response):
    return response


def get_random_header():
    """返回一个随机的头"""
    return {'User-Agent': str(UserAgent().random)}


def limit_text(s: str, max_len, replace='...'):
    """文本太长自动打省略号"""
    s_len = len(s)
    replace_len = len(replace)
    if s_len + replace_len > max_len:
        return s[:int(max_len / 2)] + replace + s[-int(max_len / 2):]
    else:
        return s


def elem_tostring(elem):
    """HTML元素转换成字符串"""
    elem_text_nodes = elem.xpath(".//text()")
    beautiful_text = ''.join([elem.strip() for elem in elem_text_nodes])
    return beautiful_text


def good_dirname(string: str) -> str:
    """一个好目录名字"""
    string.replace('\n', '').replace('\t', '').replace(' ', '')
    string = limit_text(string, 60, '___')
    return string


def get_sqlite_db(db_name='db.sqlite'):
    db = SqliteDatabase(db_name)
    logger.info('创建数据库[{}]'.format(db_name))
    return db


def random_sleeper(a, b):
    def sleeper():
        sleep(random.randint(a, b))

    return sleeper


class ProxyGeneratorBase:
    def __call__(self, *args, **kwargs) -> Iterable:
        ...
