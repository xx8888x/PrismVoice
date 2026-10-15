"""稜鏡擷取服務：唯一的新聞擷取管線。

    python main.py                 # 常駐：每分鐘檢查哪些來源到期（依 sources.fetch_interval_minutes）
    python main.py --once          # 只跑一輪到期的來源
    python main.py --source cna    # 立即抓取指定來源（即使停用或未到期）
    python main.py --backfill-content  # 補抓還沒有全文的舊文章（每次最多 100 篇），再補做轉載比對
"""
import argparse
import logging
import sys
import time

import pymysql

from prism.pipeline import backfill_contents, backfill_duplicates, run_due
from prism.settings import db_config

TICK_SECONDS = 60


def main():
    parser = argparse.ArgumentParser(description='Prism RSS ingestion')
    parser.add_argument('--once', action='store_true', help='run one pass over due sources and exit')
    parser.add_argument('--source', help='fetch this source slug now, then exit')
    parser.add_argument('--backfill-content', action='store_true', help='fetch missing full text, check unchecked bodies for reprints, then exit')
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding='utf-8')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    log = logging.getLogger('prism')
    single_run = args.once or args.source or args.backfill_content

    while True:
        try:
            conn = pymysql.connect(**db_config())
            try:
                if args.backfill_content:
                    backfill_contents(conn)
                    backfill_duplicates(conn)
                else:
                    run_due(conn, slug=args.source, force=bool(args.source))
            finally:
                conn.close()
        except pymysql.err.OperationalError as error:
            log.error('資料庫連線失敗：%s', error)
            if single_run:
                return 1
        if single_run:
            return 0
        time.sleep(TICK_SECONDS)


if __name__ == '__main__':
    sys.exit(main())
