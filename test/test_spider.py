import os
import sys

sys.path.append(os.pardir)

import logging

from spider import Spider
from spider import ResourceRoot

spider = Spider()
logger = logging.getLogger('spider')
res = ResourceRoot('resources/imgs')


class TestResponse:
    def test_css(self):
        r = spider.get('https://www.baidu.com/')
        r.encoding = 'gb2313'
        result = r.css('title')[0]
        assert result.text == '百度一下，你就知道'


class TestSpider:
    def test_resource(self):
        # logger.debug('list_dir: {}', res.list_dir)
        # logger.debug('files: {}', str(res.files))
        # logger.debug('dirs: {}', str(res.dirs))
        # logger.debug('root_dir: {}', str(res.root_dir))
        hello = res['hello']

        # res2 = ResourceRoot('res2')
        # res2['hello2'] = res
        logger.debug(hello)

        # f.seek(0)
        # print(f.read())

    def test_spider(self):
        resp = spider.get('http://www.baidu.com/', '1.png', timeout=1)
        resp.encoding = 'gb2313'
        # print(resp.text)
        print('=====================')
        spider.cache.save()


def test_gs():
    # spider.cache.clear_all()
    r = spider.get('www.baidu.com/', 's',
                   params={'wd': 'python我爱你'},
                   cache=Spider.DISABLE_CACHE)
    print('r.type', type(r))
    print(r)
    # print(r.text)
