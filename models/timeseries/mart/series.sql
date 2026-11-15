{# 系列の一覧。検索サイトの表示順 (layer1〜layer5) に並べる #}

select *
from {{ ref('stg_series') }}
order by db, layer1, layer2, layer3, layer4, layer5, series_code
