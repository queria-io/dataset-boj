{# 値を型付けする。DB はファイルのフォルダ名から取る。
   期は期種ごとに桁が違う: 暦年・年度は YYYY、半期は YYYYHH (01・02)、四半期は YYYYQQ (01〜04)、
   月次・週次・日次は API が返す形のまま (月次は YYYYMM) #}

select
    upper(regexp_extract(filename, 'data/([^/]+)/observations[^/]*\.csv\.gz$', 1)) as db,
    series_code,
    period,
    cast(left(period, 4) as integer) as year,
    cast(value as double) as value
from {{ ref('raw_observations') }}
