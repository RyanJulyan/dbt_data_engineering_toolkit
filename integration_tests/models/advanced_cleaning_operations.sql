with source_data as (
    select *
    from {{ ref('stg_cleaning_operations') }}
),

statistics as (
    select
        *,
        {{ dbt_data_engineering_toolkit.percentile('amount_filled', 0.25) }} as amount_q1,
        {{ dbt_data_engineering_toolkit.percentile('amount_filled', 0.75) }} as amount_q3,
        {{ dbt_data_engineering_toolkit.standard_score('amount_filled') }} as amount_standard_score
    from source_data
)

select
    *,
    {{ dbt_data_engineering_toolkit.string_title("'hello world'") }} as title_example,
    {{ dbt_data_engineering_toolkit.string_capitalize("'hELLO WORLD'") }} as capitalize_example,
    {{ dbt_data_engineering_toolkit.string_left_strip("'  left'") }} as left_strip_example,
    {{ dbt_data_engineering_toolkit.string_right_strip("'right  '") }} as right_strip_example,
    {{ dbt_data_engineering_toolkit.string_remove_whitespace("'  inner space  '") }} as whitespace_example,
    {{ dbt_data_engineering_toolkit.string_pad("'x'", 3, 'left', '_') }} as pad_example,
    {{ dbt_data_engineering_toolkit.string_regex_extract("'abc-123'", '([0-9]+)', 1) }} as regex_example,
    {{ dbt_data_engineering_toolkit.string_replace_many("'old cat'", {'old': 'new', 'cat': 'dog'}) }} as replace_example,
    {{ dbt_data_engineering_toolkit.string_regex_replace_many("'red cat'", {'r.d': 'blue', 'cat': 'dog'}) }} as regex_replace_example,
    {{ dbt_data_engineering_toolkit.string_translate_chars("'abc'", {'a': '1', 'b': '2', 'c': '3'}) }} as translate_example,
    {{ dbt_data_engineering_toolkit.replace_outside_bounds('amount_filled', 0, 100, 50) }} as amount_replaced,
    {{ dbt_data_engineering_toolkit.within_bounds('amount_filled', 0, 100) }} as amount_in_bounds,
    {{ dbt_data_engineering_toolkit.log_transform('amount_filled', 10) }} as amount_log,
    {{ dbt_data_engineering_toolkit.is_iqr_anomaly('amount_filled', 'amount_q1', 'amount_q3', 0.5) }} as amount_iqr_anomaly,
    {{ dbt_data_engineering_toolkit.is_modified_zscore_anomaly('amount_filled', 25, 30, 3.5) }} as amount_modified_zscore_anomaly
from statistics
