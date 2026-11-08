-- 1 行が 1 系列の 1 期
select db, series_code, period, count(*) as n
from {{ ref('observations') }}
group by all
having count(*) > 1
