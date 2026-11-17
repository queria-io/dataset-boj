{# 値。pipelines/boj.py が DB ごとに、取り直した系列を data/<db>/observations.csv.gz に、
   公開中のバージョンから写した系列を data/<db>/observations_previous.csv.gz に書く。取得したままの形。
   2 つを 1 つの read_csv で読むと後のファイルの行が落ちることがあったので、別々に読んで足す #}

{% set files = ['observations', 'observations_previous'] %}
{% for name in files %}
select *
from read_csv(
    'data/*/{{ name }}.csv.gz',
    header = true,
    filename = true,
    columns = {'series_code': 'VARCHAR', 'period': 'VARCHAR', 'value': 'VARCHAR'}
)
{% if not loop.last %}union all{% endif %}
{% endfor %}
