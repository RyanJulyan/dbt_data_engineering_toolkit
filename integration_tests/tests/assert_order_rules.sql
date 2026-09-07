select *
from {{ ref('stg_orders') }}
where
    (order_id in ('o-1', 'o-3') and array_length(exceptions) <> 0)
    or (order_id = 'o-2' and array_length(exceptions) <> 3)

