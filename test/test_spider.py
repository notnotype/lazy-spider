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
