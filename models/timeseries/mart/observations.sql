{# 値に系列の期種を付ける。系列コードで引くことが多いので、DB・系列コード・期の順に並べる #}

select
    o.db,
    o.series_code,
    s.frequency,
    o.period,
    o.year,
    o.value
from {{ ref('stg_observations') }} as o
join {{ ref('stg_series') }} as s using (db, series_code)
order by o.db, o.series_code, o.period
