-- 1 行が 1 系列の 1 期
select series_code, period, count(*) as n
from {{ ref('tankan_observations') }}
group by all
having count(*) > 1
