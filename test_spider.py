import logging

from spider import Spider

logger = logging.getLogger('sss.s')

if __name__ == '__main__':
    spider = Spider()
    spider.get('www.baidu.com')
    logger.info('hello')
