# 快速入门
> 此文档意在使你快速了解此项目的使用

# 豆瓣爬虫
> 我们通过一个实例来讲解此模块的用法
>
你可以在 [`/examples/douban_spider.py`](../examples/douban_spider.py) 处看到完整的代码

## 预览

### 下面给出大致的代码
```python
import logging

from lazy_spider import *

spider = Spider()
logger = logging.getLogger('lazy_spider')
res = ResourceRoot('resources')

if __name__ == '__main__':
    url = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start={}'
    for each in range(0, 400, 20):
        res['douban.json'] = spider.get(url.format(each)).json
```

##### 是不是感到很惊讶呢?

##### 其实代码还能够更加简短

```python
from lazy_spider import *
spider = Spider()
res = ResourceRoot('resources')
url = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start={}'
for each in range(0, 400, 20):
    res['douban.json'] = spider.get(url.format(each)).json
```

你尝试运行它, 然后你能看见你当前目录多了一个叫 `resources` 的文件夹

并且, 该文件夹里面有一个 `douban.json` 文件

这就是此程序的输出结果了

## 讲解

##### 我现在给出注释版本

```python
import logging
from time import sleep

# 导入此项目
from lazy_spider import Spider, ResourceRoot

# 实例化一个 `Spider` 类
# 这是你与网络的接口类, 也是此模块的主要类
spider = Spider()
# 模块内置的 `logger` 你可以尝试用 `logger.debug` 来代替 `print` 这会更加美观
logger = logging.getLogger('lazy_spider')
# 模块里面的管理资源文件的类, 它把一个资源文件夹抽象成了一个类
res = ResourceRoot('resources')

if __name__ == '__main__':
    url = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start={}'
    for each in range(0, 400, 20):
        logger.info('url: {}', each)
        
        # 把爬虫获得的api转化成json存入资源文件夹下的 `douban.json` 文件中
        # res['douban.json'] = lazy_spider.get(url.format(each)).json
        # 这样的逻辑是 -- 把网页转化成 `json` 对象 -- 把 `json` 对象 转换成文本对象
        # 你可以尝试这样, 去掉后面的 `.json`
        # res['douban.json'] = lazy_spider.get(url.format(each))
        # 而这样的逻辑是 -- 直接把网页存入文件
        res['douban.json'] = spider.get(url.format(each)).json
        sleep(5)

```

# 然后

你就自己看源码把, 在我懒得在写文档之前QAQ
