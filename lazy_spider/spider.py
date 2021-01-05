import datetime
import json
import logging
import os
import re
import shutil
import time
import uuid
from json import loads
from os.path import exists
from os.path import join
from time import localtime
from time import sleep
from types import MethodType
from typing import Union, IO, List, Callable
from urllib.parse import urljoin, quote

import requests
from lxml.etree import HTML
from lxml.html import HtmlElement

from lazy_spider.cache import SqliteCache
from .utils import generic_response_pipeline, get_random_header, limit_text, random_sleeper


# 改变脚本的工作目录
# START_DIR = os.getcwd()
# FILE_DIR = os.path.dirname(os.path.abspath(__file__))
# os.chdir(FILE_DIR)


class FormatFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> int:
        def getMessage(obj):
            msg = str(obj.msg)
            if obj.args:
                msg = msg.format(*obj.args)
            return msg

        # 使用`{`风格格式化
        record.getMessage = MethodType(getMessage, record)

        # context: dict = record.__getattribute__('context')
        # record.msg += '\n' + '\n'.join([f'{str(k)}: {str(v)}' for k, v in context.items()])

        return True


# todo 继承`StreamHandler`实现详细`log`与精简`log`
# todo 记录错误单独保存文件
def init_logger(log_dir='log', level=logging.DEBUG) -> logging.Logger:
    # os.chdir(START_DIR)
    if not exists(log_dir):
        os.makedirs(log_dir)
    file_handler = logging.FileHandler(f"{log_dir}/"
                                       f"{localtime().tm_year}-"
                                       f"{localtime().tm_mon}-"
                                       f"{localtime().tm_mday}--"
                                       f"{localtime().tm_hour}h-"
                                       f"{localtime().tm_min}m-"
                                       f"{localtime().tm_sec}s.log",
                                       encoding="utf-8")
    formatter = logging.Formatter('[{levelname!s:5}]'
                                  '[{asctime}]'
                                  '[{name!s:^6}]'
                                  '[{lineno!s:4}行]'
                                  '[{module}.{funcName}]\n'
                                  '{message!s}',
                                  style='{',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    _logger = logging.getLogger('lazy_spider')
    _console = logging.StreamHandler()
    _logger.setLevel(level)
    _console.setLevel(level)

    _logger.addHandler(file_handler)
    _console.setFormatter(formatter)

    _logger.addHandler(file_handler)
    _logger.addHandler(_console)
    _logger.addFilter(FormatFilter())
    # os.chdir(FILE_DIR)
    return _logger


logger = init_logger()


class ResourceBase:
    """ResourceRoot的无意义基类"""

    def serialize_as_folder(self, path):
        pass


# 考虑使用`property`
class ResourceRoot(ResourceBase):
    # todo 没有 close
    def scan(self):
        """扫描当前文件夹, 更新`list_dir`, `files`, `dirs`"""
        self.list_dir = list(map(lambda name: join(self.root_dir, name), os.listdir(self.root_dir)))

        file_names = list(filter(lambda name: os.path.isfile(name), self.list_dir))
        self.files = {filename: None for filename in file_names}
        dir_names = [_dir for _dir in filter(lambda name: os.path.isdir(name), self.list_dir)]
        self.dirs = {dir_name: ResourceRoot(dir_name) for dir_name in dir_names}

    def __init__(self, root_dir='resources', chuck=2048, mode='r+'):
        """把一个文件夹抽象成一个类,可以保存和读取资源文件

        :key root_dir: 默认为`resources`
        :key chuck: 默认读取写入的区块
        :key mode: 文件打开模式  默认`r+`
        """
        self.rel_root_dir = root_dir
        self.chuck = chuck
        self.root_dir = os.path.abspath(root_dir)
        self.__mode = mode
        # self.__encoding = encoding

        # These Attributes will be 初始化 before long
        self.list_dir = None
        self.files = None
        self.dirs = None

        if not exists(self.root_dir):
            os.makedirs(self.root_dir)
            logger.info('创建root_dir {}', self.root_dir)

        self.scan()

    @property
    def mode(self):
        return self.__mode

    @mode.setter
    def mode(self, value):
        self.__mode = value

    @staticmethod
    def __guess_file_mode(filename):
        """根据文件名, 或者 `url` 来猜测使用哪一种模式打开文件"""
        if filename.lower().endswith((
                '.jpg', '.png'
        )):
            mode = 'wb'
        else:
            mode = 'w'
        return mode

    def __getitem__(self, name: str) -> IO:
        name = join(self.root_dir, name)
        if name in self.files.keys():
            if self.files[name] is None or self.files[name].closed:
                mode = self.__guess_file_mode(name)
                if 'b' not in mode:
                    self.files[name] = open(name, mode=mode)
                else:
                    self.files[name] = open(name, mode=mode, encoding='w')
            return self.files[name]
        elif name in self.dirs.keys():
            return self.dirs[name]
        else:
            raise KeyError('不存在此文件')

    def __setitem__(self, filename: str, value: Union[str, IO, dict, ResourceBase, bytes]):
        """默认调用`self.save`"""
        filename = filename.format(
            now=datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S'),
            uuid=uuid.uuid4().__str__().replace('-', ''),
            time=time.time().__str__().replace('.', '')
        )
        self.save(filename, value)

        # todo 低效率
        self.scan()

    def __contains__(self, name: str):
        return name in self.list_dir

    def __str__(self):
        # return '<ResourceRoot root_dir=\'{}\'>'.format(self.root_dir)
        return '<ResourceRoot {!r}>'.format(self.list_dir)

    def create_sub_root(self, name):
        name = join(self.root_dir, name)
        if not exists(name):
            os.mkdir(name)
        sub_root = ResourceRoot(name)
        self.dirs[name] = sub_root
        return sub_root

    def serialize_as_folder(self, path):
        """把自己的一个复制复制到一个位置"""
        shutil.copytree(self.rel_root_dir, os.path.realpath(path))

    def save(self, name, value: Union[str, IO, dict, ResourceBase, bytes], **kwargs):
        """传入文件名,和一个`流`, 或者`字符串`, 或者`ResourceRoot`, 保存文件后,流将被关闭
            自动覆盖

        :param name: 文件名你要保存在这个`ResourceRoot`下的
        :param value: 它可能是一个`str`对象, 或者`IO`流对象, 或者是一个`dict`字典,如果传入`dict`则会被转换成`json`文本保存
        """
        # 如果是 `ResourceBase` 类
        if isinstance(value, ResourceBase):
            value.serialize_as_folder(join(self.root_dir, name))
            logger.debug('保存目录成功[{}]', join(self.root_dir, name))
        else:  # 是字符串或流
            path = join(self.root_dir, name)
            encoding = kwargs.get('encoding', None)
            # 如果是字典, 则把字典转换为字符串
            if isinstance(value, dict):
                f = open(path, mode='w', encoding=encoding)
                json.dump(value, f, indent=4, ensure_ascii=False)
                # 如果是字符串
            elif isinstance(value, str):
                f = open(path, mode='w', encoding=encoding)
                f.write(value)
            elif isinstance(value, bytes):
                f = open(path, 'wb')
                f.write(value)
            # 如果是流
            elif isinstance(value, IO):
                f = open(path, 'wb')
                f.write(value.read())
            else:
                raise RuntimeError('不支持传入此类型{}'.format(type(value)))
            logger.debug('保存文件成功[{}]', join(self.root_dir, name))

    def close(self):
        ...


# 抽象来使用 `pipeline`
class Spider:
    # todo 针对每次请求不同的`header`来重新加载缓存
    # todo 增加字段`data`,存`post`字段
    # todo 增加字段`header`, 存header

    # 强制使用缓存
    FORCE_CACHE = 2
    # 运行使用缓存
    ENABLE_CACHE = 1
    # 不使用缓存
    DISABLE_CACHE = 0

    # done `lxml`
    class Response:
        def __init__(self, response: requests.Response):
            self.response = response
            self.status_code = response.status_code
            self.__html = None
            self.__json = None
            self.__title = None

        @property
        def history(self):
            return self.response.history

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
        def url(self):
            return self.response.url

        @property
        def html(self) -> HtmlElement:
            if self.__html is None:
                self.__html = HTML(self.text)
            return self.__html

        def xpath(self, exp) -> List[HtmlElement]:
            return self.html.xpath(exp)

        def css(self, css) -> List[HtmlElement]:
            return self.html.cssselect(css)

        @property
        def json(self, *args, slices=None, **kwargs) -> dict:
            """
            :keyword slices: (start, end)字符串分片后在进行解码
            """
            if not self.__json:
                try:
                    if slices:
                        self.__json = loads(self.text[slices[0]: slices[1]], *args, **kwargs)
                    else:
                        self.__json = loads(self.text, *args, **kwargs)
                except json.JSONDecodeError:
                    logger.error("Json解码错误{}", self.text)
                    raise
            return self.__json

        def search(self, pattern, flags=0):
            return re.search(pattern, self.text, flags=flags)

        @property
        def ok(self):
            return self.response.ok

        @property
        def title(self):
            if not self.__title:
                result = self.__title = self.xpath('//title/text()')
                if result:
                    self.__title = result[0]
                else:
                    self.__title = "Error"
            return self.__title

        def __repr__(self):
            return '<Response[{}] [{}]>'.format(
                self.response.status_code,
                self.title
            )

        def __str__(self):
            return self.__repr__()

    def __init__(self):
        self.headers_generator = get_random_header
        # self.cache = JsonCache()
        self.cache = SqliteCache()
        self.session = requests.session()
        self.sleeper = random_sleeper(5, 10)
        # todo change to pipelines
        self.response_pipeline = generic_response_pipeline
        self.request_pipeline = None
        # todo proxy_generator
        self.proxy_generator = None
        self.__encoding = None
        self.update_headers()

    def set_sleeper(self, sleeper: Callable):
        if not isinstance(sleeper, Callable):
            raise RuntimeError('参数必须是Callable')
        self.sleeper = sleeper

    def set_header_generator(self, header_generator):
        # if not isinstance(header_generator, Callable):
        #     raise RuntimeError('参数必须是Callable')
        self.headers_generator = header_generator

    def set_response_pipeline(self, response_pipeline):
        # if not isinstance(response_pipeline, Callable):
        #     raise RuntimeError('参数必须是Callable')
        self.response_pipeline = response_pipeline

    def set_request_pipeline(self, request_pipeline):
        # if not isinstance(request_pipeline, Callable):
        #     raise RuntimeError('参数必须是Callable')
        self.request_pipeline = request_pipeline

    def set_proxy_generator(self, proxy_generator):
        # if not isinstance(proxy_generator, Callable):
        #     raise RuntimeError('参数必须是Callable')
        self.proxy_generator = proxy_generator

    @property
    def encoding(self):
        return self.__encoding

    @encoding.setter
    def encoding(self, encoding):
        self.__encoding = encoding

    def set_cookie(self, cookie: str):
        """设置cookie
        :param cookie: 一个 `cookie` 字符串
        """
        cookie = {'Cookie': cookie}
        self.session.cookies = requests.sessions.cookiejar_from_dict(
            cookie,
            cookiejar=None,
            overwrite=True)

    def lunch(self, handle: [requests.get, requests.post], *args, **kwargs) -> \
            Union[Response, requests.Response, object]:
        """

        :param handle 处理请求的一个函数
        :param kwargs: 包含`requests`库所有选项
        :keyword alive_time: Union[datetime, int]缓存存活日期
        :keyword cache: 是否使用缓存
        :keyword sep_time: 间隔时间

        :return: Union[Response, requests.Response, object]
        """
        # 获取`alive_time`, `url`参数
        kwargs.setdefault('alive_time', datetime.datetime.now() + datetime.timedelta(days=3))
        kwargs.setdefault('cache', True)
        kwargs.setdefault('timeout', (5, 20))
        kwargs.setdefault('retry', 3)
        alive_time = kwargs.pop('alive_time')
        sep_time = kwargs.get('sep_time', self.sleeper)
        cache_enable = kwargs.pop('cache')
        retry = kwargs.pop('retry')

        url = ''
        for each in args:
            url = urljoin(url, each)
        if '://' not in url:
            url = 'http://' + url
            logger.debug('url没有添加协议, 使用[http]协议代替')

        is_force_cache = cache_enable == self.FORCE_CACHE

        # 如果 `is_force_cache` is True 则, 不论缓存是否过期, 都从缓存加载
        if self.cache.is_cached(url, ignore_date=is_force_cache) and cache_enable:
            logger.debug('从缓存: {} <- {}', limit_text(url, 200), self.cache.table_name)
            return self.cache.from_cache(url, force=is_force_cache)

        if cache_enable == Spider.DISABLE_CACHE:
            # 如果禁用这个url的缓存, 则将之从缓存文件删除
            self.cache.clear_cache(url)

        class HTTPBadCodeError(RuntimeError):
            ...

        # 发送请求
        # 显示logger文案
        if 'params' in kwargs:
            params = kwargs.get('params')
            tmp = ['{}={}'.format(k, quote(v)) for k, v in params.items()]
            logger.info('请求: {}', limit_text(url + '?' + '&'.join(tmp), 200))
        else:
            logger.info('请求: {}', limit_text(url, 200))

        retry = retry
        while retry:
            try:
                # 间隔时间
                response = self.Response(handle(url, **kwargs))
                if isinstance(sep_time, Callable):
                    sep_time()
                else:
                    sleep(sep_time)
                if len(response.response.history) >= 1:
                    history = [each.url for each in response.response.history]
                    history.append(response.url)
                    logger.debug('页面重定向: {}',
                                 '->'.join(['[{}]'.format(i) for i in history]))
                if response.response.ok:
                    if cache_enable == Spider.ENABLE_CACHE:
                        self.cache.cache(response.url, response, alive_time)
                else:
                    raise HTTPBadCodeError(f'坏HTTP响应', response)
                return response
            except requests.Timeout as e:
                if retry == 1:
                    raise e
                logger.debug('超时,重试---{}'.format(str(4 - retry)))
            except requests.RequestException as e:
                if retry == 1:
                    logger.error('取消重试---{}'.format(str(4 - retry)))
                    raise e
                logger.error('HTTP报错---{}'.format(str(4 - retry)))
                # todo 对于失败的`url`保存到另一个`log`文件
            except HTTPBadCodeError as e:
                if retry == 1:
                    logger.info('坏HTTP响应, 取消重试({})'.format(e.args[1].status_code))
                    return e.args[1]
                logger.debug('坏HTTP响应({})---{}', e.args[1].status_code, 4 - retry)
            finally:
                retry -= 1

    def get(self, *args, **kwargs) -> [Response, requests.Response, object]:
        """获取网页

        :param args: (元组)`url`的各个路径:
        :param kwargs: 包含`requests`库所有选项
        :keyword alive_time: Union[datetime, int]缓存存活日期
        :keyword cache: 是否使用缓存
        :keyword sep_time: 间隔时间

        :return: Union[Response, requests.Response, object]
        """
        # 获取`alive_time`, `url`参数
        resp = self.lunch(self.session.get, *args, **kwargs)
        if self.response_pipeline:
            resp = self.response_pipeline(self, resp)
        return resp

    def post(self, *args, **kwargs) -> Response:
        """获取网页

        :param args: (元组)`url`的各个路径:
        :param kwargs: 包含`requests`库所有选项
        :keyword alive_time: Union[datetime, int]缓存存活日期
        :keyword cache: 是否使用缓存
        :keyword sep_time: 间隔时间

        :return: Union[Response, requests.Response, object]
        """
        resp = self.lunch(self.session.post, *args, **kwargs)
        if self.response_pipeline:
            resp = self.response_pipeline(self, resp)
        return resp

    def update_headers(self):
        """调用`self.headers_generator`来更新头"""
        if self.headers_generator:
            self.session.headers.update(self.headers_generator())

    def close(self):
        self.session.close()


local = {}


def get_spider():
    if 'lazy_spider' not in local:
        local['lazy_spider'] = Spider()
    return local['lazy_spider']


def gs():
    """qs() == get_spider()"""
    return get_spider()


def get(*args, **kwargs):
    gs().get(*args, **kwargs)


def post(*args, **kwargs):
    gs().post(*args, **kwargs)


def close():
    gs().close()
