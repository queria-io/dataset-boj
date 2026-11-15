select
    db,
    name,
    field
from {{ ref('raw_databases') }}
