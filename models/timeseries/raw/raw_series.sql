{# 系列の一覧。pipelines/boj.py が DB ごとに data/<db>/series.csv に書く。取得したままの形 #}

select * from read_csv('data/*/series.csv', header = true, all_varchar = true, filename = true)
