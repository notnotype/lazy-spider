import logging
import os
import json
import uuid
import pickle
import datetime

from lxml.etree import HTML
from os.path import join
from os.path import exists
from typing import Any, Union
from urllib.parse import urljoin
from json import load, dump
from time import localtime

import requests
from requests import get as _get
from requests import post as _post

logger: logging.Logger = Any


def limit_text(s: str, max_len):
    """文本太长自动打省略号"""
    s_len = len(s)
    if s_len + 3 > max_len:
        return s[:int(max_len / 2)] + '...' + s[-int(max_len / 2):]
    else:
        return s


# todo 继承`StreamHandler`实现详细`log`与精简`log`
# todo 记录错误单独保存文件
def init_logger(log_dir='log', level=logging.INFO):
    global logger
    logger = logging.Logger('__main__')
    if not exists(log_dir):
        os.mkdir(log_dir)
    handler = logging.FileHandler(f"{log_dir}/"
                                  f"{localtime().tm_year}-"
                                  f"{localtime().tm_mon}-"
                                  f"{localtime().tm_mday}--"
                                  f"{localtime().tm_hour}h-"
                                  f"{localtime().tm_min}m-"
                                  f"{localtime().tm_sec}s.log",
                                  encoding="utf-8")
    formatter = logging.Formatter("[%(levelname)-5.5s][%(funcName)-16.16s][%(lineno)3.3d行]-[%(message)s]")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)

    logger.addHandler(handler)
    logger.addHandler(console)


# todo 管理文件
class FilePipeline:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def process(self, item):
        ...

    def close(self):
        ...


class HeadersGenerator:
    # todo maybe not staticmethod
    @staticmethod
    def get_headers() -> dict:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'}

    def __call__(self, *args, **kwargs):
        return self.get_headers()


class Spider:
    # done `lxml`
    class Response:
        def __init__(self, response: requests.Response):
            self.response = response
            self.status_code = response.status_code
            self.__html = None

        @property
        def content(self):
            return self.response.content

        @property
        def text(self):
            return self.response.text

        @property
        def encoding(self):
            return self.response.encoding

        @encoding.setter
        def encoding(self, encoding):
            self.response.encoding = encoding

        @property
        def html(self) -> HTML:
            if not self.__html:
                self.__html = HTML(self.text)
            return self.__html

        @html.setter
        def html(self, value):
            self.__html = value

        def xpath(self, exp):
            return self.__html.xpath(exp)

    # todo 针对每次请求不同的`header`来重新加载缓存
    # todo 增加字段`data`,存`post`字段
    # todo 增加字段`header`, 存header
    class Cache:
        """
        __init__
        cache
        from_cache
        is_cached
        close
        """

        def __init__(self, cache_dir='__pycache__'):
            self.__cache_dir = cache_dir
            self.__cache_json_name = 'cache.json'
            if not exists(cache_dir):
                os.mkdir(cache_dir)
                # TODO right?
                logger.debug('生成文件缓存路径: ', os.path.realpath(cache_dir))
            # 是否存在`cache.json`,没有则生成
            if not exists(join(cache_dir, self.__cache_json_name)):
                try:
                    with open(join(self.__cache_dir, self.__cache_json_name), 'a+', encoding='utf8') as f:
                        dump({"cached_files": {}}, f, indent=4)
                except IOError as e:
                    logger.error('IO错误: {}'.format(join(self.__cache_dir, self.__cache_json_name)))
                    raise e
            # 打开缓存清单文件
            try:
                with open(join(cache_dir, self.__cache_json_name), 'r', encoding='utf8') as f:
                    self.__cache_json: dict = load(f)
            except IOError as e:
                logger.exception(e)
                logger.error('IO错误: {}'.format(join(cache_dir, self.__cache_json_name)))
                raise e
            except json.JSONDecodeError as e:
                logger.error('Json解码错误: {}'.format(join(cache_dir, self.__cache_json_name)))
                raise e
            except Exception as e:
                logger.error('未知错误在: {}'.format(join(cache_dir, self.__cache_json_name)))
                raise e

        def is_cached(self, name: str) -> bool:
            if name in self.__cache_json['cached_files'].keys():
                item = self.__cache_json['cached_files'][name]
                alive_time: datetime.datetime = datetime.datetime.strptime(item['alive_time'], '%Y-%m-%d %H:%M:%S')
                if alive_time > datetime.datetime.now():
                    return True
                else:
                    logger.debug('存活时间已过,重新缓存')
                    return False
            else:
                return False

        def from_cache(self, name: str) -> object:
            if self.is_cached(name):
                item = self.__cache_json['cached_files'][name]
                filename = item['filename']
                with open(join(self.__cache_dir, filename), 'rb') as f:
                    return pickle.load(f)
            else:
                return None

        def cache(self, name: str, obj: object, alive_time: datetime.datetime) -> bool:
            if self.is_cached(name):
                return True
            else:
                self.__cache_json['cached_files'][name] = {
                    "filename": str(uuid.uuid4()),
                    "typing": str(obj.__class__),
                    "repr": repr(obj),
                    "alive_time": alive_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                item = self.__cache_json['cached_files'][name]
                filename = item['filename']
                try:
                    with open(join(self.__cache_dir, filename), 'wb') as f:
                        pickle.dump(obj, f)
                        self.save()
                except IOError:
                    logger.error('IO错误: {}'.format(filename))
                    return False
                else:
                    logger.debug('缓存: {:.200} -> {}'.format(limit_text(name, 200), filename))
                    return True

        # 关闭保存文件
        def save(self):
            try:
                with open(join(self.__cache_dir, self.__cache_json_name), 'r+', encoding='utf8') as f:
                    dump(self.__cache_json, f, indent=4)
            except IOError as e:
                logger.error('IO错误: {}'.format(join(self.__cache_dir, self.__cache_json_name)))
                raise e

    def __init__(self):
        self.header_enable = True
        self.header_generator = HeadersGenerator()
        self.cache = Spider.Cache()

    # todo 对于失败的`url`保存到另一个`log`文件
    def __get_or_post(self, *args, **kwargs) -> Union[Response, requests.Response, object]:
        """

        :param args `url`的各个路径:
        :param kwargs: 包含`requests`库所有选项
        :param alive_time: 缓存存活日期
        :param cache_enable: 是否使用缓存
        :param sep_time: 间隔时间
        :return:
        """
        # 获取`alive_time`, `url`参数
        kwargs.setdefault('alive_time', datetime.datetime.now() + datetime.timedelta(days=3))
        kwargs.setdefault('cache_enable', True)
        handle = args[1]
        alive_time = kwargs.pop('alive_time')
        cache_enable = kwargs.pop('cache_enable')
        args = args[2:]

        # 是否使用头
        if self.header_enable:
            kwargs['headers'] = self.header_generator()

        url = '/'
        for each in args:
            url = urljoin(url, each)
        if self.cache.is_cached(url) and cache_enable:
            logger.debug('从缓存: {:.200} <- {}'.format(limit_text(url, 200), '文件'))
            return self.cache.from_cache(url)
        logger.info('下载: {:.200}'.format(limit_text(url, 200)))

        retry = 3
        while retry:
            try:
                response = self.Response(handle(*args, **kwargs))
                if response.status_code == 200:
                    self.cache.cache(url, response, alive_time)
                else:
                    logger.debug('状态码[{}], 取消缓存'.format(response.status_code))
                return response
            except requests.Timeout as e:
                if retry == 1:
                    raise e
                logger.debug('超时,重试---' + str(4 - retry))
            except requests.RequestException as e:
                if retry == 1:
                    logger.error('取消重试---' + str(4 - retry))
                    raise e
                logger.error('HTTP报错---' + str(4 - retry))
            finally:
                retry -= 1

    def get(self, *args, **kwargs) -> Response:
        """
        args `url`的各个路径:\n
        kwargs: 包含`requests`库所有选项\n
        alive_time: 缓存存活日期\n
        cache_enable: 是否使用缓存\n
        sep_time: 间隔时间\n
        """
        # 获取`alive_time`, `url`参数
        return self.__get_or_post(self, _get, *args, **kwargs)

    def post(self, *args, **kwargs) -> Response:
        """
        args `url`的各个路径:\n
        kwargs: 包含`requests`库所有选项\n
        alive_time: 缓存存活日期\n
        cache_enable: 是否使用缓存\n
        sep_time: 间隔时间\n
        """
        return self.__get_or_post(self, _post, *args, **kwargs)


init_logger(level=logging.DEBUG)
if __name__ == '__main__':
    spider = Spider()
    resp = spider.get('http://www.baidu.com/', '1.png', timeout=1, cache_enable=False)
    resp.encoding = 'gb2313'
    print(resp.text)
    print('=====================')
    spider.cache.save()
