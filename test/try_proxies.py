"""爬代理"""

import os
import sys

sys.path.append(os.pardir)

import threading
from math import ceil

from lazy_spider.utils import get_sqlite_db
from lazy_spider.generic.proxy import *


def clear_proxies(checker: GenericProxyChecker, pool: SqliteProxyPool, proxies):
    for proxy in proxies:
        try:
            r = checker.proxy_info(proxy)
            if r == checker.CANT_TELNET:
                print(f'cant telnet[{str(proxy)}]')
            elif r == checker.CANT_PROXY:
                print(f'\033[1;44;31mcant proxy[{str(proxy)}]\033[0m')
            else:
                print(f'\033[1;42;31m[{str(proxy)}]好耶\033[0m')

            # del proxy
            if r == checker.CANT_TELNET:
                _, _, host, port = parse_proxy_url(list(proxy.values())[0])
                del_cont = pool.del_proxy(str(host), int(port))
                if not del_cont:
                    print('del_cont:', del_cont)
        except Exception as e:
            logger.exception(e)


def main():
    checker = GenericProxyChecker(Apis('223.156.141.144'))
    checker.set_sock_timeout(1)
    pool = SqliteProxyPool(get_sqlite_db())

    threading_counts = 40
    check_counts = 800
    proxies = pool.get_proxies(check_counts)

    threads = []
    partial = ceil(len(proxies) / threading_counts)
    for i in range(0, len(proxies), partial):
        temp = slice(i, i + partial)
        each_process = proxies[temp]
        print('thread start')
        t = threading.Thread(target=clear_proxies, args=(checker, pool, each_process))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


if __name__ == '__main__':
    exit(main())
