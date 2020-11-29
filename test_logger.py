import logging
from logging import LogRecord
from types import MethodType
from typing import Any

logger: logging.Logger = Any


class MyHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        print('My Handler __init__')

    def emit(self, record: LogRecord) -> None:
        super().emit(record)
        for k, v in record.__dict__.items():
            print('{:20.20}:   {:20.20} {:20.20}'.format(str(k), str(v), str(type(v))))
        print('My Handler')


class FormatFilter(logging.Filter):

    def filter(self, record: LogRecord) -> int:
        def getMessage(obj):
            msg = str(obj.msg)
            if obj.args:
                msg = msg.format(*obj.args)
            return msg

        # 使用`{`风格格式化
        record.getMessage = MethodType(getMessage, record)

        # context: dict = record.__getattribute__('context')
        # record.msg += '\n' + '\n'.join([f'{str(k)}: {str(v)}' for k, v in context.items()])

        return True


def init_logger(level=logging.DEBUG):
    global logger
    logger = logging.Logger(__name__)
    formatter = logging.Formatter('[{asctime}]'
                                  '[{levelname!s:5}]'
                                  '[{name!s:^16}]'
                                  '[{lineno!s:4}行]'
                                  '[{module}.{funcName}]\n'
                                  '{message!s}',
                                  style='{',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    console_err_handler = logging.StreamHandler()
    console_err_handler.setLevel(level)
    console_err_handler.setFormatter(formatter)

    format_filter = FormatFilter()

    logger.addHandler(console_handler)
    logger.addHandler(console_err_handler)

    logger.addFilter(format_filter)


if __name__ == '__main__':
    init_logger()
    # logger.info('info{}', 'a', extra={'context': {'ip': 123}})
    logger.info('info{}', 'a')
