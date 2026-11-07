{# 系列の一覧。pipelines/boj.py が DB ごとに data/<db>/series.csv に書く。
   検索サイトの表示順 (layer1〜layer5) に並べる #}
select
    upper(regexp_extract(filename, 'data/([^/]+)/series\.csv$', 1)) as db,
    series_code,
    name,
    name_en,
    nullif(unit, '') as unit,
    nullif(unit_en, '') as unit_en,
    frequency,
    category,
    category_en,
    cast(layer1 as integer) as layer1,
    cast(layer2 as integer) as layer2,
    cast(layer3 as integer) as layer3,
    cast(layer4 as integer) as layer4,
    cast(layer5 as integer) as layer5,
    start_period,
    end_period,
    strptime(last_update, '%Y%m%d')::date as last_update,
    nullif(notes, '') as notes,
    nullif(notes_en, '') as notes_en
from read_csv('data/*/series.csv', header = true, all_varchar = true, filename = true)
order by db, layer1, layer2, layer3, layer4, layer5, series_code
