{# 値。pipelines/boj.py が DB ごとに data/<db>/observations.csv.gz に書く。取得したままの形 #}

select *
from read_csv(
    'data/*/observations.csv.gz',
    header = true,
    filename = true,
    columns = {'series_code': 'VARCHAR', 'period': 'VARCHAR', 'value': 'VARCHAR'}
)
