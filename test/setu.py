import logging
import time

from spider import Spider, ResourceRoot

spider = Spider()
logger = logging.getLogger('spider')
res = ResourceRoot('resources/imgs')


def hg():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.57',
        'referer': 'https://setu.awsl.ee/setu!'
    }
    return headers


spider.headers_generator = hg

if __name__ == "__main__":
    for i in range(10, 20):
        tmp = '{:13.13}'.format(time.time()).replace('.', '')
        res[str(i) + '.jpg'] = spider.get(
            'https://setu.awsl.ee/api/setu!?w=' + tmp,
            cache=Spider.DISABLE_CACHE).content
        time.sleep(0.1)
    # f = res['1.jpg']
    # tmp = '{:13.13}'.format(time.time()).replace('.', '')
    # r = spider.get('https://setu.awsl.ee/api/setu!?w=' + tmp,
    #                cache=Spider.DISABLE_CACHE)
    # f.write(r.content)
