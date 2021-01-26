import datetime
import json
import logging
import os
import shutil
import time
import uuid
from logging import getLogger
from os.path import exists
from os.path import join
from time import localtime
from types import MethodType
from typing import Union, IO

from fake_useragent import UserAgent
from peewee import SqliteDatabase

logger = getLogger('lazy_spider')
__all__ = (
    'get_random_header',
    'limit_text',
    'good_dirname',
    'get_sqlite_db',
    'get_logger',
    'register_default_logger',
    'ResourceBase',
    'ResourceRoot'
)


# todo 优化logger 有颜色的logger
class FormatFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> int:
        def getMessage(obj):
            msg = str(obj.msg)
            if obj.args:
                msg = msg.format(*obj.args)
            return msg

        # 使用`{`风格格式化
        record.getMessage = MethodType(getMessage, record)
        return True


# todo 继承`StreamHandler`实现详细`log`与精简`log`
# todo 记录错误单独保存文件
def register_default_logger(log_dir='log', level=logging.DEBUG) -> logging.Logger:
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
    # generic logger
    formatter = logging.Formatter('[{levelname!s:5}]'
                                  '[{asctime}]'
                                  '[{name!s:^6}]'
                                  '[{lineno!s:4}行]'
                                  '[{module}.{funcName}]\n'
                                  '{message!s}',
                                  style='{',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    # todo colorful logger
    # formatter = logging.Formatter('[{levelname!s:5}]'
    #                               '[{asctime}]'
    #                               '[{name!s:^6}]'
    #                               '[{lineno!s:4}行]'
    #                               '[{module}.{funcName}]\n'
    #                               '{message!s}',
    #                               style='{',
    #                               datefmt='%Y-%m-%d %H:%M:%S')
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
    return _logger


def get_logger():
    return getLogger('lazy_spider')


def get_random_header():
    """返回一个随机的头"""
    return {'User-Agent': str(UserAgent().random)}


def limit_text(s: str, max_len, replace='...'):
    """文本太长自动打省略号"""
    s_len = len(s)
    replace_len = len(replace)
    if s_len + replace_len > max_len:
        return s[:int(max_len / 2)] + replace + s[-int(max_len / 2):]
    else:
        return s


def good_dirname(string: str) -> str:
    """一个好目录名字"""
    string.replace('\n', '').replace('\t', '').replace(' ', '')
    string = limit_text(string, 60, '___')
    return string


def get_sqlite_db(db_name='db.sqlite'):
    db = SqliteDatabase(db_name)
    logger.info('获取数据库[{}]'.format(db_name))
    return db



class ResourceBase:
    """ResourceRoot的无意义基类"""

    def serialize_as_folder(self, path):
        pass


# todo 考虑使用`property`
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
