import logging
import sys

from lazy_spider import *

sys.path.append('../')

spider = Spider()
logger = logging.getLogger('lazy_spider')
res = ResourceRoot('resources')

if __name__ == '__main__':
    url = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start={}'
    for each in range(0, 400, 20):
        print('url: {}'.format(each))
        res['douban.json'] = spider.get(url.format(each)).json
