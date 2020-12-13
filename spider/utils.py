import logging

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


def limit_text(s: str, max_len):
    """文本太长自动打省略号"""
    s_len = len(s)
    if s_len + 3 > max_len:
        return s[:int(max_len / 2)] + '...' + s[-int(max_len / 2):]
    else:
        return s


def elem_tostring(elem):
    """HTML元素转换成字符串"""
    elem_text_nodes = elem.xpath(".//text()")
    beautiful_text = ''.join([elem.strip() for elem in elem_text_nodes])
    return beautiful_text


def good_dirname(string: str) -> str:
    string.replace('\n', '').replace('\t', '').replace(' ', '')
    return string


def get_sqlite_db(db_name='db.sqlite'):
    db = SqliteDatabase(db_name)
    logger.info('创建数据库[{}]'.format(db_name))
    return db
