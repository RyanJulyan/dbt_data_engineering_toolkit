with counts as (
    select
        (select count(*) from {{ ref('stg_customer_events') }}) as staged_rows,
        (select count(*) from {{ ref('stg_customer_events_valid') }}) as valid_rows,
        (select count(*) from {{ ref('stg_customer_events_rejected') }}) as rejected_rows
)

select *
from counts
where staged_rows <> 3
   or valid_rows <> 2
   or rejected_rows <> 1
