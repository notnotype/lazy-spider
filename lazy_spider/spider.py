import random
import time
from time import sleep
from typing import Union, Callable, Literal, Optional, Tuple, List

import requests
from requests import PreparedRequest
from requests.sessions import Session

from lazy_spider.cache import SqliteCache
from lazy_spider.exception import HTTPBadCodeError
from lazy_spider.http import Response
from lazy_spider.typing import T_Headers
from lazy_spider.utils import (
    get_random_header,
    limit_text,
    get_logger
)
from .cache import CacheBase, NoCache
from .generic import ProxyPoolBase
from .typing import T_Sleeper, T_Headers_Generator

logger = get_logger()

__all__ = (
    'ResponseMiddlewareBase',
    'RequestMiddlewareBase',
    'HeadersGeneratorBase',
    'RandomHeaderGenerator',
    'SleeperBase',
    'RandomTimeSleeper',
    'NoSleeper',
    'Spider',
    'get_spider',
    'gs', 'get', 'post', 'close'
)


# todo
class RequestMiddlewareBase:
    def __call__(self, spider: 'Spider', request: 'PreparedRequest') -> 'requests.Request':
        ...


class ResponseMiddlewareBase:
    def __call__(self, spider: 'Spider', request: 'Response') -> 'Response':
        ...


class HeadersGeneratorBase:
    def __call__(self, spider: 'Spider') -> T_Headers:
        ...


class RandomHeaderGenerator(HeadersGeneratorBase):
    def __call__(self, *args, **kwargs):
        return get_random_header()


class SleeperBase:
    def __call__(self, *args, **kwargs):
        ...


class SepTimeSleeper(SleeperBase):
    def __init__(self, sep_time):
        self.sep_time = sep_time
        self.__last_request_time: Optional[int] = None

    def wait_sep_time(self):
        if self.__last_request_time:
            now = time.time()
            sleep_time = self.sep_time - (now - self.__last_request_time)
            self.__last_request_time = now
            if sleep_time > 0:
                sleep(sleep_time)


class RandomTimeSleeper(SleeperBase):
    def __init__(self, a: int, b: int):
        self.a = a
        self.b = b

    def __call__(self, *args, **kwargs):
        sleep(random.randint(self.a, self.b))


class NoSleeper(SleeperBase):
    def __call__(self, *args, **kwargs):
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

    cache: CacheBase
    session: Session
    headers_generator: T_Headers_Generator
    sleeper: T_Sleeper
    request_middlewares: List[RequestMiddlewareBase]
    response_middlewares: List[ResponseMiddlewareBase]
    proxy_pool: Optional[ProxyPoolBase]
    __encoding: str

    cache_mode: Literal[0, 1, 2]
    timeout: Tuple[int, int]
    alive_time: int
    retry: int

    def __init__(
            self,
            cache: Optional[CacheBase] = None,
            session: Optional[Session] = None,
            headers_generator: Optional[T_Headers_Generator] = None,
            sleeper: Optional[T_Sleeper] = None,
            request_middlewares: Optional[List[RequestMiddlewareBase]] = None,
            response_middlewares: Optional[List[ResponseMiddlewareBase]] = None,
            proxy_pool: Optional[ProxyPoolBase] = None,
            __encoding: Optional[str] = None,

            cache_mode: Optional[Literal[0, 1, 2]] = None,
            timeout: Optional[Tuple[int, int]] = None,
            alive_time: Optional[int] = None,
            retry: Optional[int] = None,
    ):
        self.cache = cache or NoCache()
        if not session:
            self.session = Session()
        # if not headers_generator:
        #     self.headers_generator =
        self.sleeper = sleeper or NoSleeper()
        self.request_middlewares = request_middlewares or []
        self.response_middlewares = response_middlewares or []
        self.proxy_pool = proxy_pool
        self.__encoding = __encoding
        # todo
        self.headers_generator = headers_generator or get_random_header

        self.cache_mode = cache_mode or Spider.DISABLE_CACHE
        self.timeout = timeout or (5, 5)
        self.alive_time = alive_time or 3
        self.retry = retry or 3

    @classmethod
    def get_cache_spider(cls) -> 'Spider':
        spider = cls(SqliteCache())
        spider.cache_mode = Spider.ENABLE_CACHE
        return spider

    def set_sleeper(self, sleeper: T_Sleeper):
        if not isinstance(sleeper, Callable):
            raise RuntimeError('参数必须是Callable')
        self.sleeper = sleeper

    # todo getter and setter

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

    def add_request_middlewares(
            self, request_middlewares: Union[RequestMiddlewareBase, List[RequestMiddlewareBase]]):
        if isinstance(request_middlewares, list):
            self.request_middlewares.extend(request_middlewares)
        else:
            self.request_middlewares.append(request_middlewares)

    def add_response_middlewares(
            self, response_middlewares: Union[ResponseMiddlewareBase, List[ResponseMiddlewareBase]]):
        if isinstance(response_middlewares, list):
            self.response_middlewares.extend(response_middlewares)
        else:
            self.response_middlewares.append(response_middlewares)

    def remove_request_middlewares(self, request_middlewares):
        del self.request_middlewares[request_middlewares]

    def remove_response_middlewares(self, response_middlewares):
        del self.response_middlewares[response_middlewares]

    def get_response(
            self, req: PreparedRequest, timeout=None, allow_redirects=True, cache_mode=None,
            alive_time=None, retry=None
    ):
        """低级 api 发送请求， 在这里进行 request_middleware， response_middleware 的处理"""

        cache_mode = cache_mode or self.cache_mode
        alive_time = alive_time or self.alive_time
        timeout = timeout or self.timeout
        retry = retry or self.retry

        cache_signal = req.url

        if cache_mode == Spider.DISABLE_CACHE:
            # 如果禁用这个url的缓存, 则将之从缓存文件删除
            self.cache.clear_cache(cache_signal)

        # 如果 `is_force_cache` is True 则, 不论缓存是否过期, 都从缓存加载
        elif cache_mode == Spider.FORCE_CACHE and self.cache.is_cached(cache_signal, ignore_date=True):
            logger.debug('从缓存: {} <- {}', limit_text(req.url, 100), self.cache)
            return self.cache.from_cache(cache_signal, force=True)

        elif cache_mode == Spider.ENABLE_CACHE and self.cache.is_cached(cache_signal, ignore_date=False):
            logger.debug('从缓存: {} <- {}', limit_text(cache_signal, 100), self.cache)
            return self.cache.from_cache(cache_signal, force=False)

        retry = retry
        while retry:
            try:
                # 间隔时间
                response = self.session.send(
                    req, timeout=timeout or (5, 5), allow_redirects=allow_redirects
                )
                if self.encoding:
                    response.encoding = self.encoding
                response = Response(response)

                self.sleeper()

                if len(response.response.history) >= 1:
                    history = [each.url for each in response.response.history]
                    history.append(response.url)
                    logger.debug('页面重定向: {}',
                                 '->'.join(['[{}]'.format(i) for i in history]))
                if response.response.ok:
                    if cache_mode == Spider.ENABLE_CACHE:
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

    def lunch(
            self, method, url, *, cache_mode=None, alive_time=None, timeout=None, retry=None,
            headers=None, data=None, params=None, cookies=None, hooks=None
    ):
        """高级 api 发送请求， 处理网页缓存等功能"""
        # 发送请求
        req = requests.Request(
            method=method.upper(),
            url=url,
            headers=headers,
            files=None,
            data=data or {},
            json=None,
            params=params or {},
            auth=None,
            cookies=cookies,
            hooks=hooks,
        )
        req = self.session.prepare_request(req)
        for request_middleware in self.request_middlewares:
            req = request_middleware(self, req)

        resp = self.get_response(
            req, cache_mode=cache_mode, alive_time=alive_time, timeout=timeout, retry=retry
        )

        for response_middleware in self.response_middlewares:
            resp = response_middleware(self, resp)
        return resp

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
        resp = self.lunch('get', *args, **kwargs)
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
        resp = self.lunch('post', *args, **kwargs)
        return resp

    def update_headers(self):
        """调用`self.headers_generator`来更新头"""
        self.session.headers.update(self.headers_generator())

    def close(self):
        self.session.close()


# todo 脚本模式和项目模式
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
