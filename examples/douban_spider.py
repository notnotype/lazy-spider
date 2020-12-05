import logging
import sys
from time import sleep

# 导入此项目
from spider import Spider, ResourceRoot

# 把父级目录添加到 `path` 中
# 不然无法导入此项目
sys.path.append('../')

# 实例化一个 `Spider` 类
# 这是你与网络的接口类, 也是此模块的主要类
spider = Spider()
# 模块内置的 `logger` 你可以尝试用 `logger.debug` 来代替 `print` 这会更加美观
logger = logging.getLogger('spider')
# 模块里面的管理资源文件的类, 它把一个资源文件夹抽象成了一个类
res = ResourceRoot('resources')

spider.headers_generator = lambda x: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.55'}

if __name__ == '__main__':
    url = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start={}'
    for each in range(0, 400, 20):
        logger.info('url: {}', each)

        # 把爬虫获得的api转化成json存入资源文件夹下的 `douban.json` 文件中
        # res['douban.json'] = spider.get(url.format(each)).json
        # 这样的逻辑是 -- 把网页转化成 `json` 对象 -- 把 `json` 对象 转换成文本对象
        # 你可以尝试这样, 去掉后面的 `.json`
        # res['douban.json'] = spider.get(url.format(each))
        # 而这样的逻辑是 -- 直接把网页存入文件
        res['douban.json'] = spider.get(url.format(each)).json
        sleep(5)
