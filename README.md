# 日本銀行 時系列統計

日本銀行の[時系列統計データ検索サイト](https://www.stat-search.boj.or.jp/)の API 機能で取得した統計を、SQL で集計できるテーブルにしたデータセットです。

| スキーマ | 統計 | 期種 |
| --- | --- | --- |
| `tankan` | 短観（全国企業短期経済観測調査） | 四半期・年度・年度半期 |
| `cgpi` | 企業物価指数 | 月次 |
| `sppi` | 企業向けサービス価格指数 | 月次・四半期 |
| `loans_by_sector` | 貸出先別貸出金 | 四半期・月次 |

各スキーマに次の 2 つのテーブルがあります。

| テーブル | 内容 |
| --- | --- |
| `series` | 系列の一覧。1 行が 1 系列。系列名称・単位・期種・分類・検索サイトでの並び順（`layer1`〜`layer5`） |
| `observations` | 値。1 行が 1 系列の 1 期。`series_code` で `series` と結合します |

## 出典と利用条件

- 出典: 日本銀行「時系列統計データ検索サイト」
- このサービスは、日本銀行時系列統計データ検索サイトの API 機能を使用しています。サービスの内容は日本銀行によって保証されたものではありません
- 利用条件は[日本銀行の著作権・免責事項](https://www.boj.or.jp/about/copyright.htm)と[API 機能利用時の留意点](https://www.stat-search.boj.or.jp/info/api_notice.pdf)に従います
- 値は変えず、API が返した系列コード・期・値をそのまま収録しています

## 使い方

短観の業況判断 D.I.（全規模・全産業・実績）の推移:

```sql
SELECT o.period, o.value
FROM boj.tankan.observations AS o
WHERE o.series_code = 'TK99F0000601GCQ00000'
ORDER BY o.period;
```

系列は `series` の名称で探します。企業物価指数の 2020 年基準の総平均:

```sql
SELECT series_code, name, unit
FROM boj.cgpi.series
WHERE category LIKE '企業物価指数 2020年基準%' AND name LIKE '%総平均%';
```

## 収録範囲の注意

- 期（`period`）の桁は期種で違います。年・年度は `YYYY`（年度は 4 月から翌年 3 月）、半期は `YYYYHH`（`01` が上期）、四半期は `YYYYQQ`（`01`〜`04`）、月次は `YYYYMM` です。`year` と `sub_period` に分けた列もあります
- 物価指数は基準年（1995〜2020 年）ごとに別の系列です。基準年をまたいで並べるときは、`series` の `category` と `unit` で基準年を確認してください
- 総平均と内訳、総貸出と業種別のように、合計と内訳の系列が並んでいます。足し合わせると重複します
- 値の無い期の行はありません

## ビルド

```bash
git submodule update --init
uv sync
scripts/build.sh   # fdl checkout → python main.py → fdl commit
```

全系列を取り直します。API に負荷をかけないよう、リクエストの間を 1 秒以上空けています。
