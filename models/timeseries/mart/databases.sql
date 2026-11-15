{# 検索サイトの DB の一覧。系列の数は系列の一覧から数える #}

select
    d.db,
    d.name,
    d.field,
    count(s.series_code) as series_count
from {{ ref('stg_databases') }} as d
left join {{ ref('stg_series') }} as s using (db)
group by all
order by d.db
