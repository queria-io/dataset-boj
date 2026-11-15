{# 系列の一覧を型付けする。DB はファイルのフォルダ名から取る #}

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
from {{ ref('raw_series') }}
