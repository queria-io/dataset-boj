-- 取得した DB は、どれも系列が 1 つ以上ある
select db
from {{ ref('databases') }}
where series_count = 0
