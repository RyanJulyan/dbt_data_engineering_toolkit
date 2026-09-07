with counts as (
    select
        (select count(*) from {{ ref('stg_customers_valid') }}) as valid_count,
        (select count(*) from {{ ref('stg_customers_rejected') }}) as rejected_count
)
select * from counts where valid_count <> 1 or rejected_count <> 2

