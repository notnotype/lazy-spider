import logging
import sys

from spider import Spider

sys.path.append('../')

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    spider = Spider()
    spider.get('www.baidu.com')
    logger.info('hello')
