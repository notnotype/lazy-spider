# light-spider
 一个配置完备的爬虫工具
 对 lxml, requests, peewee......的二次封装
 A lazy spider tools which intergrate lxml, requests, peewee......

# 快速开始
> 使用 `pip` 安装
```bash
pip install lazy_spider
```
> 然后编写`Python`代码

> 拿出你最喜欢的编辑器, 输入以下代码

并保存为 `my_first.py` 放在此项目的根目录下, 然后打开终端输入 `python my_first.py` 来运行
```python
import logging
import sys
from urllib.parse import quote

from spider import *


spider = Spider()
logger = logging.getLogger('spider')
res = ResourceRoot('resources')

if __name__ == '__main__':
    resp = spider.get('www.baidu.com/s?wd={}'.format(quote('美女')), cache=False)
    hrefs = resp.xpath('//a/@href')
    res['href.json'] = {'hrefs': hrefs}

```
在这个例子中我们爬取了 `www.baidu.com` 下 `美女` 关键词下第一页的链接

并把它们保存在了 `resources/href.json` 文件下

```res['href.json'] = {'hrefs': hrefs}```

这一句就是保存json到文件的代码

一切都是那么的自然而简单,仅仅只需按以下方法调用就能将json序列化了
```python
# 使用`spider`模块
# res['文件名'] = 字典对象
# res['href.json']={'hrefs':hrefs}
```
相比原生实现, `spider` 模块不仅能够帮助你处理复杂的目录结构了

你不需要在你的代码里面使用大量类似 ```os.path.join(dir_name, file_name)```的
代码了,因为 `spider` 模块已经帮你抽象成 `ResourceRoot` 类了
```python
# 原生实现
import json
import os
f =  open(os.path.join('resources', 'hrefs.json'), 'w')
f.write(json.loads({'hrefs': hrefs}))
f.close()
```
此伪代码和上面的伪代码完成了一样的事情

他们都把一个名为 `hrefs` 保存在 `resources/href.json` 目录下

但是, 很明显, 第一种方法更加方便和简洁

---

除此之外 `light-spider` 能够很硬气的对 get方法返回对象`resp`直接调用`xpath`方法

你不需要担心效率,因为 `resp.xpath` 是懒惰的, 它只会在你使用它的时候才去请求资源

```python
resp = spider.get('www.baidu.com/s?wd={}'.format(quote('美女')), cache=False)
hrefs = resp.xpath('//a/@href')
```

####  你注意到了没有
```python
resp = spider.get('www.baidu.com/s?wd={}'.format(quote('美女')), cache=False)
```
`get` 的参数没有添加 `http://` 协议, 但是脚本依然能够运行.

原因是因为 `light-spider` 自动检测你是否带有协议, 并且用 `http://` 作为你的默认协议

####  `cache`参数是什么?
是缓存(bool类型) 来告诉 `light-spider` 这次请求是否要缓存

#### 想看更多?
这里有[快速入门](docs/quick_start.md)指南


# 特色
> `light-spider`对什么进行了`二次封装`?

> 资源目录被抽象成 `ResourceRoot` 类了 能够帮助你处理复杂的目录结构

### 她对哪一些库进行了`二次封装`?
- `lxml`		 `解析html`
- `request`	  `网络请求库`
- `urllib3`	    `网络请求库`
- `pickle`	   `Python序列化库`
- `logging`	  `Python日志模块`
- `json`		`python json模块`
- `re`           `python 正则表达式`

### 比较方便的地方
- 网站请求缓存 
> 不用担心断点续爬了!
- 内置日志(`logger`)
> 更好看的控制台输出!
- 请求容错
> 不用自己手写容错代码啦!
- `Spider`类耦合`HTML`, `Response`,等类
> 更加方便了!

# 更新日志
- `2020/12/3`
```
更新了ResourceRoot类
这个类可也方便json等文件的读取与写入
```
- `2020/12/6`
```
更改了项目结构
考虑使用 `Item` 类来收集资源
像 `scrapy` 一样
同时 也更新了 `READEME.md`, 增加了快速入门文档 `quick_start.md`
```
- `2020/12/13`
```
集成 `peewee`
```

- `2020/12/19`
```
使用`poetry`来管理依赖
```

