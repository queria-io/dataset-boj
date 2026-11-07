"""日本銀行 時系列統計データ検索サイトの API から、DB ごとの系列のメタ情報と値を取得する。

API の仕様: https://www.stat-search.boj.or.jp/info/api_manual.pdf
- メタデータ API で DB の全系列 (系列コード・名称・単位・期種・階層) を取る
- コード API に同じ期種の系列コードを 250 件ずつ渡して値を取る。1 回に返る値は
  60,000 件までで、超えた分は NEXTPOSITION から続きを取る
- 高頻度のアクセスは接続を切られることがあるので、リクエストの間を空ける
"""

import csv
import gzip
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger("pipelines")

BASE = "https://www.stat-search.boj.or.jp/api/v1"
BATCH = 250
INTERVAL_SEC = 1.0

SERIES_FIELDS = [
    "series_code", "name", "name_en", "unit", "unit_en", "frequency",
    "category", "category_en", "layer1", "layer2", "layer3", "layer4", "layer5",
    "start_period", "end_period", "last_update", "notes", "notes_en",
]
SERIES_KEYS = [
    "SERIES_CODE", "NAME_OF_TIME_SERIES_J", "NAME_OF_TIME_SERIES", "UNIT_J", "UNIT",
    "FREQUENCY", "CATEGORY_J", "CATEGORY", "LAYER1", "LAYER2", "LAYER3", "LAYER4",
    "LAYER5", "START_OF_THE_TIME_SERIES", "END_OF_THE_TIME_SERIES", "LAST_UPDATE",
    "NOTES_J", "NOTES",
]


def get(api: str, **params) -> dict:
    url = f"{BASE}/{api}?" + urllib.parse.urlencode({"format": "json", "lang": "jp", **params})
    request = urllib.request.Request(
        url, headers={"Accept-Encoding": "gzip", "User-Agent": "queria-dataset-boj"}
    )
    for attempt in range(5):
        time.sleep(INTERVAL_SEC * (2**attempt))
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
            data = json.loads(body)
        except (OSError, ValueError) as e:
            logger.warning(f"  retry {api} ({e})")
            continue
        if data.get("STATUS") == 200:
            return data
        # 503 はデータベースへのアクセスエラー。少し待てば通る
        if data.get("STATUS") in (500, 503):
            logger.warning(f"  retry {api} ({data.get('MESSAGE')})")
            continue
        raise RuntimeError(f"{api} {params}: {data.get('STATUS')} {data.get('MESSAGE')}")
    raise RuntimeError(f"{api} {params}: gave up")


def fetch_series(db: str) -> list[dict]:
    """系列のメタ情報。系列コードの無い行は階層の見出しなので捨てる。

    同じ系列が階層の複数の場所に出てくる (企業向けサービス価格指数の類別など)。
    メタ情報は階層の順に並んでいるので、最初に出てきた場所を残す。
    """
    rows = get("getMetadata", db=db)["RESULTSET"]
    series = {}
    for r in rows:
        if r["SERIES_CODE"] and r["SERIES_CODE"] not in series:
            series[r["SERIES_CODE"]] = dict(zip(SERIES_FIELDS, (r.get(k) for k in SERIES_KEYS)))
    return list(series.values())


def fetch_values(db: str, codes: list[str]):
    """同じ期種の系列コードの値を (系列コード, 期, 値) で返す。値の無い期 (null) は返さない。"""
    position = 1
    while position:
        data = get("getDataCode", db=db, code=",".join(codes), startPosition=position)
        for r in data["RESULTSET"]:
            values = r.get("VALUES") or {}
            for period, value in zip(values.get("SURVEY_DATES", []), values.get("VALUES", [])):
                if value is not None:
                    yield r["SERIES_CODE"], period, value
        position = data.get("NEXTPOSITION")


def download(db: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    series = fetch_series(db)
    with open(out_dir / "series.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SERIES_FIELDS)
        writer.writeheader()
        writer.writerows(series)
    logger.info(f"  {db}: {len(series)} series")

    by_frequency: dict[str, list[str]] = {}
    for s in series:
        by_frequency.setdefault(s["frequency"], []).append(s["series_code"])

    count = 0
    with gzip.open(out_dir / "observations.csv.gz", "wt", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["series_code", "period", "value"])
        for frequency, codes in by_frequency.items():
            for i in range(0, len(codes), BATCH):
                for row in fetch_values(db, codes[i : i + BATCH]):
                    writer.writerow(row)
                    count += 1
            logger.info(f"  {db} {frequency}: {len(codes)} series, {count} values so far")
    logger.info(f"  {db}: {count} values")
