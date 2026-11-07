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

# 検索サイトの全 DB。DB 名・DB 名称・統計分野は API マニュアルの「DB 名」の表のとおり
DATABASES = [
    ("IR01", "基準割引率および基準貸付利率（従来「公定歩合」として掲載されていたもの）の推移", "金利（預金・貸出関連）"),
    ("IR02", "預金種類別店頭表示金利の平均年利率等", "金利（預金・貸出関連）"),
    ("IR03", "定期預金の預入期間別平均金利", "金利（預金・貸出関連）"),
    ("IR04", "貸出約定平均金利", "金利（預金・貸出関連）"),
    ("FM01", "無担保コールＯ／Ｎ物レート（毎営業日）", "マーケット関連"),
    ("FM02", "短期金融市場金利", "マーケット関連"),
    ("FM03", "短期金融市場残高", "マーケット関連"),
    ("FM04", "コール市場残高", "マーケット関連"),
    ("FM05", "公社債発行・償還および現存額", "マーケット関連"),
    ("FM06", "公社債消化状況（利付国債）", "マーケット関連"),
    ("FM07", "（参考）国債窓口販売額・窓口販売率（2004年1月まで）", "マーケット関連"),
    ("FM08", "外国為替市況", "マーケット関連"),
    ("FM09", "実効為替レート", "マーケット関連"),
    ("PS01", "各種決済", "決済関連"),
    ("PS02", "フェイルの発生状況", "決済関連"),
    ("MD01", "マネタリーベース", "預金・マネー・貸出"),
    ("MD02", "マネーストック", "預金・マネー・貸出"),
    ("MD03", "マネタリーサーベイ", "預金・マネー・貸出"),
    ("MD04", "（参考）マネーサプライ（M2+CD）増減と信用面の対応", "預金・マネー・貸出"),
    ("MD05", "通貨流通高", "預金・マネー・貸出"),
    ("MD06", "日銀当座預金増減要因と金融調節（実績）", "預金・マネー・貸出"),
    ("MD07", "準備預金額", "預金・マネー・貸出"),
    ("MD08", "業態別の日銀当座預金残高", "預金・マネー・貸出"),
    ("MD09", "マネタリーベースと日本銀行の取引", "預金・マネー・貸出"),
    ("MD10", "預金者別預金", "預金・マネー・貸出"),
    ("MD11", "預金・現金・貸出金", "預金・マネー・貸出"),
    ("MD12", "都道府県別預金・現金・貸出金", "預金・マネー・貸出"),
    ("MD13", "貸出・預金動向", "預金・マネー・貸出"),
    ("MD14", "定期預金の残高および新規受入高", "預金・マネー・貸出"),
    ("LA01", "貸出先別貸出金", "預金・マネー・貸出"),
    ("LA02", "日本銀行貸出", "預金・マネー・貸出"),
    ("LA03", "その他貸出残高", "預金・マネー・貸出"),
    ("LA04", "コミットメントライン契約額、利用額", "預金・マネー・貸出"),
    ("LA05", "主要銀行貸出動向アンケート調査", "預金・マネー・貸出"),
    ("BS01", "日本銀行勘定", "金融機関バランスシート"),
    ("BS02", "民間金融機関の資産・負債", "金融機関バランスシート"),
    ("FF", "資金循環", "資金循環"),
    ("OB01", "日本銀行の対政府取引", "その他の日本銀行関連"),
    ("OB02", "日本銀行が受入れている担保の残高", "その他の日本銀行関連"),
    ("CO", "短観", "短観"),
    ("PR01", "企業物価指数", "物価"),
    ("PR02", "企業向けサービス価格指数", "物価"),
    ("PR03", "製造業部門別投入・産出物価指数", "物価"),
    ("PR04", "＜サテライト指数＞最終需要・中間需要物価指数", "物価"),
    ("PF01", "財政資金収支", "財政関連"),
    ("PF02", "政府債務", "財政関連"),
    ("BP01", "国際収支統計", "国際収支・BIS関連"),
    ("BIS", "BIS国際資金取引統計および国際与信統計の日本分集計結果", "国際収支・BIS関連"),
    ("DER", "デリバティブ取引に関する定例市場報告", "国際収支・BIS関連"),
    ("OT", "その他", "その他"),
]


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


def write_databases(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["db", "name", "field"])
        writer.writerows(DATABASES)
