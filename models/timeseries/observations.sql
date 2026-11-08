{# 値。pipelines/boj.py が DB ごとに data/<db>/observations.csv.gz に書く。
   期は期種ごとに桁が違う: 暦年・年度は YYYY、半期は YYYYHH (01・02)、四半期は YYYYQQ (01〜04)、
   月次・週次・日次は API が返す形のまま (月次は YYYYMM)。
   系列コードで引くことが多いので、DB・系列コード・期の順に並べる #}
with observations as (
    select
        upper(regexp_extract(filename, 'data/([^/]+)/observations\.csv\.gz$', 1)) as db,
        series_code,
        period,
        cast(value as double) as value
    from read_csv(
        'data/*/observations.csv.gz',
        header = true,
        filename = true,
        columns = {'series_code': 'VARCHAR', 'period': 'VARCHAR', 'value': 'VARCHAR'}
    )
)

select
    o.db,
    o.series_code,
    s.frequency,
    o.period,
    cast(left(o.period, 4) as integer) as year,
    o.value
from observations as o
join {{ ref('series') }} as s using (db, series_code)
order by o.db, o.series_code, o.period
