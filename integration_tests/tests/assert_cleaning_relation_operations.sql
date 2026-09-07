with failures as (
  select 'distinct_count' as check_name
  from {{ ref('stg_cleaning_operations') }}
  having count(*) <> 4

  union all

  select 'complete_count' as check_name
  from {{ ref('complete_cleaning_operations') }}
  having count(*) <> 4

  union all

  select 'trimmed_rows' as check_name
  from {{ ref('trimmed_cleaning_operations') }}
  having count(*) <> 2 or min(id) <> 2 or max(id) <> 2

  union all

  select 'balanced_classes' as check_name
  from (
    select category, count(*) as row_count
    from {{ ref('balanced_cleaning_operations') }}
    group by 1
  ) class_counts
  having min(row_count) <> 1 or max(row_count) <> 1 or count(*) <> 3
)

select * from failures
