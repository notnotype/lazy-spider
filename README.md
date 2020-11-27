# light-spider
 对`requests`,`lxml`等库的二次封装

## 快速使用
> 先`clone`仓库到本地, 然后安装依赖
```bash
git clone https://github.com/notnotype/light-spider.git
cd light-spider
pip install requirements.txt
```
> 然后编写`Python`代码
> 拿出你最喜欢的编辑器, 输入一下代码
```python
from spider import Spider
spider = Spider()
resp = spider.get('http://www.baidu.com/', '1.png', timeout=1, 	cache_enable=False)
resp.encoding = 'gb2313'
print(resp.text)
print('=====================')
spider.cache.save()
```

## 特色
> `light-spider`对什么进行了`二次封装`?

#### 她对哪一些库进行了`二次封装`?
- `lxml`		 `解析html`
- `request`	  `网络请求库`
- `urllib3`	    `网络请求库`
- `pickle`	   `Python序列化库`
- `logging`	  `Python日志模块`
- `json`		`python json模块`

#### 比较方便的地方
- 网站请求缓存 
> 不用担心断点续爬了!
- 内置日志(`logger`)
> 更好看的控制台输出!
- 请求容错
> 不用自己手写容错代码啦!
- `Spider`类耦合`HTML`, `Response`,等类
> 更加方便了!

