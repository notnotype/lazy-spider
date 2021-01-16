"""字体图标解析库"""
from json import load, dump
from logging import getLogger

from PIL import Image, ImageFont, ImageDraw
from aip import AipOcr
from fontTools.ttLib.ttFont import TTFont

logger = getLogger('spider')


class FontMappingBase:
    # 映射表
    def __init__(self):
        self.real_font_mapping: dict = {}

    def update(self, filename: str):
        """更新字体映射表, 或者覆盖原来的映射表

        :param filename:
        :return:
        """
        ...

    def mapping(self, text: str) -> str:
        """映射字体图标为正确的格式 (/uxxxx -> char)

        :param text:
        :return:
        """
        if not self.real_font_mapping:
            raise RuntimeError('没有调用get_mapping方法')
        else:
            trans = str.maketrans(self.real_font_mapping)
            return text.translate(trans)

    def get_font_mapping(self) -> dict:
        """获取字体映射表

        :return:
        """
        if self.real_font_mapping:
            return self.real_font_mapping
        else:
            raise RuntimeError('没有获取到映射表')

    def load_json(self, filename: str):
        """从json文件间读取字体映射表

        :param filename:
        :return:
        """
        with open(filename, 'rb') as f:
            self.real_font_mapping = load(f)

    def save_json(self, filename: str):
        """保存字体映射为json

        :param filename:
        :return:
        """
        with open(filename, 'wb') as f:
            dump(self.real_font_mapping, f)


class ORCBase:
    def recognize(self, image_path: str) -> str:
        ...


class BaiduORC(ORCBase):
    def __init__(self, app_id, api_key, secret_key):
        """基于百度orc的字体图标解析

            读取字体图标 -> pillow 绘图 -> orc识别 -> 生成字体映射表 ->
            self.mapping(text)映射 ->

        :param app_id:
        :param api_key:
        :param secret_key:
        """
        super().__init__()
        # init baidu orc
        self.orc = AipOcr(app_id, api_key, secret_key)

    def recognize(self, image_path: str) -> str:
        """调用orc识别图片

        :param image_path:
        :return str: 图片信息
        """
        f = open(image_path, 'rb')
        result = self.orc.basicGeneral(f.read())
        result = '\n'.join([k['words'] for k in result['words_result']])
        f.close()
        return result


class ORCFontMappingBase(FontMappingBase):
    def __init__(self):
        super(ORCFontMappingBase, self).__init__()
        self.real_font_mapping: dict
        self._orc: ORCBase


class BaiduORCFontMapping(ORCFontMappingBase):
    def __init__(self, app_id, api_key, secret_key):
        """基于百度orc的字体图标解析

            读取字体图标 -> pillow 绘图 -> orc识别 -> 生成字体映射表 ->
            self.mapping(text)映射 ->

        :param app_id:
        :param api_key:
        :param secret_key:
        """
        super(BaiduORCFontMapping, self).__init__()
        # init baidu orc
        self._orc = BaiduORC(app_id, api_key, secret_key)

    def update(self, filename: str, x_counts=25, y_counts=25, show_img=False):
        """更新字体映射表, 或者覆盖原来的映射表

        :param filename: 字体文件
        :param x_counts: pillow画出来的图片一行几个字
        :param y_counts: pillow画出来的图片一列几个字
        :param show_img: 展示pillow画出来的图片不?
        :return:
        """
        # open font file
        font = TTFont(filename)
        pillow_font = ImageFont.truetype(filename, 20)

        # draw font
        cmap: dict = font.getBestCmap()
        # 删除没用的字体代码
        del cmap[120]

        # get font info
        font_name = chr(list(cmap.keys())[0])
        font_size = list(pillow_font.getsize(font_name))
        font_offset = list(pillow_font.getoffset(font_name))

        font_size[0] += font_offset[0] // 2
        font_size[1] += font_offset[1] // 2

        batch_size = x_counts * y_counts
        # 连续作画
        for i in range(0, len(cmap), batch_size):
            cmap_batch = list(cmap.items())[i:i + batch_size]
            canvas_size = font_size[0] * x_counts, font_size[1] * y_counts

            # drawing
            text = ''
            for index, each in enumerate(cmap_batch):
                char = chr(each[0])
                text += char
                if (index + 1) % x_counts == 0:
                    text += '\n'

            text = text.strip()

            canvas = Image.new('RGB', canvas_size, (255, 255, 255))
            draw = ImageDraw.Draw(canvas)
            draw.text((0, 0), text, fill=0, font=pillow_font)
            if show_img:
                canvas.show()
            canvas.save('temp.jpeg', format='jpeg')

            result = self._orc.recognize('temp.jpeg')

            real_font_mapping = dict(zip(text.replace('\n', ''), result.replace('\n', '')))

            self.real_font_mapping.update(real_font_mapping)
