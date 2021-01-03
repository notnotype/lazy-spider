__author__ = 'Notnotype'

import logging

from spider import Spider

logger = logging.getLogger('spider')

from collections import deque


def generic_item_middleware(collector, item: dict):
    return item


def generic_request_middleware(collector, requests: str):
    return requests


class SpiderBase:
    start_urls = []

    def __init__(self, spider=None):
        if not spider:
            spider = Spider()

        self.spider = spider
        self.queue = deque()
        self.items = []
        self.queue += self.start_urls

        self.item_middlewares = [generic_item_middleware]
        self.request_middlewares = [generic_request_middleware]

    def process_item(self, item: dict):
        ...

    def process_request(self, request: str):
        ...

    def parse(self, response):
        yield None

    def run(self):
        ...


class GenericSpider(SpiderBase):
    def __init__(self, spider=None):
        super().__init__(spider)

    def process_item(self, item: dict):
        # logger.debug('process_item: {}', str(item))
        for each in self.item_middlewares:
            item = each(self, item)
        return item

    def process_request(self, request: str):
        # logger.debug('process_request: {}', str(request))
        for each in self.request_middlewares:
            request = each(self, request)
        return request

    def parse(self, response):
        return super().parse(response)

    def run(self):
        while self.queue:
            url = self.queue.popleft()
            url = self.process_request(url)
            response = self.spider.get(url)
            for each in self.parse(response):
                print(each, type(each))
                if isinstance(each, dict):
                    each = self.process_item(each)
                    self.items.append(each)
                elif isinstance(each, str):
                    self.queue.append(each)
                else:
                    logger.debug('No item yield, Parse next page')
