import logging
import sys

from spider.spider import Spider

sys.path.append('../')

spider = Spider()
logger = logging.getLogger('spider.test_spider')
logger.debug('heldsfadsflo')

if __name__ == '__main__':
    resp = spider.get('https://www.baidu.com', cache=False)
    result_title = resp.search('<title>(.*)</title>')
    result_title.groups()
