"""
generic_template
"""

import logging

from peewee import *

from lazy_spider import ResourceRoot
from lazy_spider import Spider

spider = Spider()
logger = logging.getLogger('lazy_spider')
res = ResourceRoot('resources')
db = SqliteDatabase('db.sqlite')


class MyModel(Model):
    url = CharField()
    data = TextField()

    class Meta:
        database = db


if __name__ == '__main__':
    r = spider.get('https://www.baidu.com/')
    r.encoding = 'gb2313'
    result = r.css('title')[0]
    logger.info(result)
    res.close()
