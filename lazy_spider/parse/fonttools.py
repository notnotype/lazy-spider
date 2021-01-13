"""字体图标解析库"""
from logging import getLogger

from PIL import Image, ImageFont, ImageDraw
from aip import AipOcr
from fontTools.ttLib.ttFont import TTFont

logger = getLogger('spider')


# todo 解耦
# todo 增加效率
class BaiduORCFontMapping:
    def __init__(self, app_id, api_key, secret_key, font_file: str = None):
        """基于百度orc的字体图标解析

            读取字体图标 -> pillow 绘图 -> orc识别 -> 生成字体映射表 ->
            self.mapping(text)映射 ->

        :param app_id:
        :param api_key:
        :param secret_key:
        :param font_file: 字体文件路径
        """

        # init baidu orc
        self.orc = AipOcr(app_id, api_key, secret_key)

        self.real_font_mapping = None

        if font_file:
            self.get_mapping(font_file)

    def _orc(self, path: str) -> str:
        """调用orc识别图片

        :param path: 图片路径
        :return str: 图片信息
        """
        f = open(path, 'rb')
        result = self.orc.basicGeneral(f.read())
        result = '\n'.join([k['words'] for k in result['words_result']])
        f.close()
        return result

    def get_mapping(self, font_file: str) -> dict:
        # open font file
        font = TTFont(font_file)
        font2 = ImageFont.truetype(font_file, 20)

        # draw font
        cmap: dict = font.getBestCmap()
        del cmap[120]

        x_counts = 25
        y_counts = 25

        # get font info
        font_name = chr(list(cmap.keys())[0])
        font_size = list(font2.getsize(font_name))
        font_offset = list(font2.getoffset(font_name))

        font_size[0] += font_offset[0] // 2
        font_size[1] += font_offset[1] // 2

        cmap_batch = list(cmap.items())[:x_counts * y_counts]
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
        draw.text((0, 0), text, fill=0, font=font2)
        canvas.show()
        canvas.save('temp.jpeg', format='jpeg')

        result = self._orc('temp.jpeg')

        real_font_mapping = dict(zip(text.replace('\n', ''), result.replace('\n', '')))

        self.real_font_mapping = real_font_mapping
        return real_font_mapping

    def mapping(self, char: str) -> str:
        """

        :param char:
        :return:
        """
        if not self.real_font_mapping:
            raise RuntimeError('没有调用get_mapping方法')
        else:
            trans = str.maketrans(self.real_font_mapping)
            return char.translate(trans)
