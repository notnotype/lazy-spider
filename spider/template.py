"""
生成模板
"""

import os
import sys

sys.path.append(os.pardir)

import logging

from spider import Spider
from spider import ResourceRoot

spider = Spider()
logger = logging.getLogger('spider')
res = ResourceRoot('resources')

if __name__ == '__main__':
    ...
