import logging
import sys
from urllib.parse import quote

from spider import *

sys.path.append('../')

spider = Spider()
logger = logging.getLogger('spider.test_spider')
res = ResourceRoot('resources')

if __name__ == '__main__':
    resp = spider.get('https://www.baidu.com/s?wd={}'.format(quote('萝莉')), cache=False)
    hrefs = resp.xpath('//a/@href')
    res['href.json'] = {'hrefs': hrefs}
