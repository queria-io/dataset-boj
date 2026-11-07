"""日本銀行 時系列統計データ検索サイトのデータパイプライン。

1. boj: 短観・企業物価指数・企業向けサービス価格指数・貸出先別貸出金の系列と値を API で取得する
2. dbt: dbt ビルド
"""

import logging
from pathlib import Path

from dbt.cli.main import dbtRunner

from pipelines.boj import download

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pipelines")

# 取得する DB。DB 名は API マニュアルの「DB 名」
DATABASES = ["CO", "PR01", "PR02", "LA01"]


def dbt_build():
    dbt = dbtRunner()
    for command in (["deps"], ["build"], ["docs", "generate"]):
        result = dbt.invoke(command)
        if not result.success:
            raise SystemExit(f"dbt {' '.join(command)} failed")


def main():
    for db in DATABASES:
        logger.info(f"boj: {db}")
        download(db, Path("data") / db.lower())

    logger.info("dbt build")
    dbt_build()


if __name__ == "__main__":
    main()
