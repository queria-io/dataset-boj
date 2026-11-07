{# 日本銀行の DB ごとの系列のメタ情報と値。pipelines/boj.py が data/<db>/ に書き出す CSV を読む。 #}

{% macro boj_series(db) %}
select
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
from read_csv('data/{{ db }}/series.csv', header = true, all_varchar = true)
order by layer1, layer2, layer3, layer4, layer5, series_code
{% endmacro %}

{#- 期は期種ごとに桁が違う: 暦年・年度は YYYY、半期は YYYYHH (01・02)、四半期は YYYYQQ (01〜04)、
    月次は YYYYMM。期種は系列のメタ情報から引く。
    系列コードで引くことが多いので、系列コード・期の順に並べる -#}
{% macro boj_observations(db) %}
with observations as (
    select series_code, cast(period as varchar) as period, cast(value as double) as value
    from read_csv(
        'data/{{ db }}/observations.csv.gz',
        header = true,
        columns = {'series_code': 'VARCHAR', 'period': 'VARCHAR', 'value': 'VARCHAR'}
    )
),

series as (
    select series_code, frequency
    from read_csv('data/{{ db }}/series.csv', header = true, all_varchar = true)
)

select
    o.series_code,
    s.frequency,
    o.period,
    cast(left(o.period, 4) as integer) as year,
    cast(nullif(substr(o.period, 5, 2), '') as integer) as sub_period,
    o.value
from observations as o
join series as s using (series_code)
order by o.series_code, o.period
{% endmacro %}
