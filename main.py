"""日本銀行 時系列統計データ検索サイトのデータパイプライン。

1. boj: 検索サイトの全 DB の系列と値を API で取得する
2. dbt: dbt ビルド
"""

import logging
from pathlib import Path

from dbt.cli.main import dbtRunner

from pipelines.boj import DATABASES, download, write_databases

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        result = dbt.invoke(command)
        if not result.success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def fetch():
    write_databases(Path("data/databases.csv"))
    for db, name, _ in DATABASES:
        logger.info(f"boj: {db} {name}")
        download(db, Path("data") / db.lower())


def main():
    fetch()
    logger.info("dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
