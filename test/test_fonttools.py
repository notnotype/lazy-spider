from configparser import ConfigParser

from lazy_spider.parse.fonttools import BaiduORCFontMapping

config = ConfigParser()
config.read('./config.ini')


def test_update():
    app_id = config.get('BaiduORC', 'AppID')
    api_key = config.get('BaiduORC', 'APIKey')
    secret_key = config.get('BaiduORC', 'SecretKey')

    fm = BaiduORCFontMapping(app_id, api_key, secret_key)

    # fm.update('fonts/c67e58f2.woff', show_img=True, strict=True)
    fm.update('fonts/f87ae77a.woff', show_img=True, strict=True)
    fm.show_character('')
    print(fm.mapping(''))
