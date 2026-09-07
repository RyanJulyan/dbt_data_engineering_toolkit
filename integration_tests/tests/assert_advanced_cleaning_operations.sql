with summary as (
  select
    min(amount_q1) as q1,
    max(amount_q3) as q3,
    sum(amount_standard_score) as score_sum
  from {{ ref('advanced_cleaning_operations') }}
),

row_failures as (
  select id
  from {{ ref('advanced_cleaning_operations') }}
  where
    title_example <> 'Hello World'
    or capitalize_example <> 'Hello world'
    or left_strip_example <> 'left'
    or right_strip_example <> 'right'
    or whitespace_example <> 'inner space'
    or pad_example <> '__x'
    or regex_example <> '123'
    or replace_example <> 'new dog'
    or regex_replace_example <> 'blue dog'
    or translate_example <> '123'
    or (id = 1 and (amount_replaced <> 50 or amount_in_bounds is not false))
    or (id = 3 and (
      amount_replaced <> 50
      or amount_in_bounds is not false
      or amount_iqr_anomaly is not true
      or amount_modified_zscore_anomaly is not true
    ))
)

select 'row_failure' as failure from row_failures
union all
select 'statistical_failure' as failure
from summary
where abs(q1 - (-1.25)) > 0.000001
   or abs(q3 - 68.75) > 0.000001
   or abs(score_sum) > 0.000001
