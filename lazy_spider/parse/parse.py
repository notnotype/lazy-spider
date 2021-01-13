import re
import warnings

from html2text import html2text
from lxml import etree
from lxml.html import HtmlElement


def elem_tostring(elem: HtmlElement, encoding='utf8'):
    """HTML元素转换成字符串"""
    warnings.warn('使用elem2text作为替代', DeprecationWarning)

    return elem2text(elem, encoding=encoding)


def elem2md(elem: HtmlElement, encoding='utf8'):
    return html2md(etree.tostring(elem, encoding=encoding))


def html2md(html: str):
    return html2text(html)


def elem2text_re(elem: HtmlElement, encoding='utf8'):
    warnings.warn('没完成', DeprecationWarning)

    html = etree.tostring(elem, encoding=encoding).decode()
    # text = re.findall(r'(<(?:.|\n)*?>)', html, re.I)
    text = re.sub(r'(<(?:.|\n)*?>)', '', html).replace('\n', '')
    print(text)
    return text


def elem2text(elem: HtmlElement, encoding='utf8'):
    """HTML元素转换成字符串"""
    elem_text_nodes = [str(e) for e in elem.xpath(".//text()") if e.isprintable()]
    beautiful_text = '\n'.join([e.strip() for e in elem_text_nodes])
    return beautiful_text


def md2text(md: str):
    warnings.warn('没完成', DeprecationWarning)
