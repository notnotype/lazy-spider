from lazy_spider import Spider
from lazy_spider.utils import get_logger

logger = get_logger()

# spider = Spider()
spider = Spider.get_cache_spider()

spider.encoding = 'gb2313'
result = spider.get('http://www.baidu.com')

print(result)
logger.debug('wdnmd')
