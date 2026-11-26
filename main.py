"""日本銀行 時系列統計データ検索サイトのデータパイプライン。

1. boj: 検索サイトの全 DB の系列を API で取得し、値は最終更新日が変わった系列だけ取得する。
   毎月 1 日 (JST) は、最終更新日を変えずに値が訂正された場合に備えて全系列の値を取り直す
2. dbt: dbt ビルド
"""

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dbt.cli.main import dbtRunner

from pipelines import boj

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        result = dbt.invoke(command)
        if not result.success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def fetch():
    boj.write_databases(Path("data/databases.csv"))
    full = datetime.now(ZoneInfo("Asia/Tokyo")).day == 1
    con = None if full else boj.previous_versions()
    if full:
        logger.info("boj: 毎月 1 日なので全系列の値を取り直す")
    try:
        latest = boj.previous_latest(con) if con else ""
        for db, name, _ in boj.DATABASES:
            logger.info(f"boj: {db} {name}")
            boj.download(db, Path("data") / db.lower(), con, latest)
    finally:
        if con:
            con.close()
    logger.info(f"boj: {boj.requests} requests")


def main():
    fetch()
    logger.info("dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
