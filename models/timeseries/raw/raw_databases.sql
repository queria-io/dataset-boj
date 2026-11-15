{# 検索サイトの DB の一覧。pipelines/boj.py が data/databases.csv に書く。取得したままの形 #}

select * from read_csv('data/databases.csv', header = true, all_varchar = true)
