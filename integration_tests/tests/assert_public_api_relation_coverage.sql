with failures as (
    select 'date_spine' as check_name
    from {{ ref('public_api_date_spine') }}
    having count(*) <> 3

    union all

    select 'deduplicate' as check_name
    from {{ ref('public_api_deduplicate') }}
    having count(*) <> 3

    union all

    select 'union_relations' as check_name
    from {{ ref('public_api_union_relations') }}
    having count(*) <> 6
)

select * from failures
