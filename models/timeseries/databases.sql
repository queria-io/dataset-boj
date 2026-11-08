{# 検索サイトの DB の一覧。pipelines/boj.py が data/databases.csv に書く。系列の数は series から数える #}
select
    d.db,
    d.name,
    d.field,
    count(s.series_code) as series_count
from read_csv('data/databases.csv', header = true, all_varchar = true) as d
left join {{ ref('series') }} as s using (db)
group by all
order by d.db
