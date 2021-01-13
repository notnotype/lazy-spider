import os
import sys

sys.path.append(os.pardir)

from lazy_spider import parse
from lxml.etree import HTML


def test_elem_tostring():
    html1 = '''<div class="cata-shop-item">
                <div class="shop-item">
                    <a href="//www.dianping.com/shop/H6qM9J3ASnzElWeo" target="_blank" class="shop-img shop-item-pic" data-category="food" data-click-title="图片" data-click-name="商家图片5" data-shopid="H6qM9J3ASnzElWeo">
                            <img lazy-src="http://p1.meituan.net/mogu/fa1ebd37c60a08925b657392fcfc937e511192.jpg%40340w_192h_1e_1l%7Cwatermark%3D0" src="http://p1.meituan.net/mogu/fa1ebd37c60a08925b657392fcfc937e511192.jpg%40340w_192h_1e_1l%7Cwatermark%3D0" alt="商户图片">
                        <div class="pic-overlay" style="display: none;"></div>
                    </a>
                    <div class="shop-info tag-no">
                        <a href="//www.dianping.com/shop/H6qM9J3ASnzElWeo" target="_blank" class="shop-name" data-category="food" data-click-title="标题" data-click-name="商家名称5" data-shopid="H6qM9J3ASnzElWeo">
                            <span class="name-desc">万食屋</span>
                        </a>
                        <div class="star-info">
                            <span class="star star-45"></span>
                            <span class="comment">628条评价</span>
                        </div>
                        <div class="area-info">
                                <span class="region-name">T淘园</span>
                                <span class="maincate-name">日本料理</span>

                        </div>
                        <div class="avg">
                                <span>¥167/人</span>
                        </div>
                    </div>
                </div>
            </div>'''
    print('======test html1======')
    text1 = parse.elem_tostring(HTML(html1))
    text2 = parse.html2md(html1)
    print(text1)
    print(text2)
