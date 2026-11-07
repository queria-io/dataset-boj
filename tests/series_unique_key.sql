-- 1 行が 1 系列。系列コードは DB の中で一意
select db, series_code, count(*) as n
from {{ ref('series') }}
group by all
having count(*) > 1
