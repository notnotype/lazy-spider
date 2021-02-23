import lazy_spider as ls
from lazy_spider import Spider


def test():
    spider = Spider.get_cache_spider()
    spider.sleeper = ls.spider.NoSleeper
    spider.encoding = 'gbk'

    keyword = 'javascrsdfsip'
    base_url = 'https://www.baidu.com/?wd={}'
    url = base_url.format(keyword)

    resp = spider.get(url)
    resp.encoding = 'gbk'
    print(resp)

    resp = spider.get(url)
    resp.encoding = 'utf8'
    print(resp)

    resp = spider.get(url)
    print(resp)

    spider.encoding = 'utf8'
    resp = spider.get(url)
    print(resp)

    spider.encoding = None
    resp = spider.get(url)
    print(resp)
