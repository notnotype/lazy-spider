import json
import re
from json import loads
from typing import List

import requests
from lxml.etree import HTML
from lxml.html import HtmlElement

from lazy_spider.utils import get_logger

logger = get_logger()
__all__ = ('Response',)


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
