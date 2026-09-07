with source as (
    select *
    from {{ ref('stg_namespace_aliases') }}
)

select
    customer_id as id,
    {{ dbt_data_engineering_toolkit.assertions_filter('exceptions') }} as assertions_filter_value,
    {{ dbt_data_engineering_toolkit.is_between('1', min_value=0, max_value=2) }} as is_between_value,
    {{ dbt_data_engineering_toolkit.is_in_list("'A'", ['A', 'B']) }} as is_in_list_value,
    {{ dbt_data_engineering_toolkit.map_value(
        "'A'", {'A': 'active'}, default='unknown', data_type='string'
    ) }} as map_value_value,
    {{ dbt_data_engineering_toolkit.mask_hash('customer_id') }} as mask_hash_value,
    {{ dbt_data_engineering_toolkit.mask_redact("'secret'") }} as mask_redact_value,
    {{ dbt_data_engineering_toolkit.normalize_whitespace("'  hello   world  '") }} as normalized_value,
    {{ dbt_data_engineering_toolkit.null_if_blank("'   '") }} as blank_value,
    {{ dbt_data_engineering_toolkit.regex_match("'abc-123'", '^[a-z]+-[0-9]+$') }} as regex_match_value,
    {{ dbt_data_engineering_toolkit.regex_replace_all("'a1b2'", '[0-9]', '') }} as regex_replace_value,
    {{ dbt_data_engineering_toolkit.rule_compare('1', '<', '2') }} as rule_compare_value,
    {{ dbt_data_engineering_toolkit.rule_one_of(["'present'", 'null']) }} as rule_one_of_value,
    {{ dbt_data_engineering_toolkit.safe_add(['1', '2']) }} as safe_add_value,
    {{ dbt_data_engineering_toolkit.safe_divide('4', '2') }} as safe_divide_value,
    {{ dbt_data_engineering_toolkit.safe_subtract(['1', '2']) }} as safe_subtract_value,
    {{ dbt_data_engineering_toolkit.standardize_code("' gb '", {'GB': 'UK'}, 2) }} as standardize_code_value,
    {{ dbt_data_engineering_toolkit.standardize_currency("' zar '") }} as standardize_currency_value,
    {{ dbt_data_engineering_toolkit.string_casefold("'AbC'") }} as string_casefold_value,
    {{ dbt_data_engineering_toolkit.string_center("'x'", 3, '_') }} as string_center_value,
    {{ dbt_data_engineering_toolkit.string_ljust("'x'", 3, '_') }} as string_ljust_value,
    {% if target.type in ['duckdb', 'bigquery', 'snowflake', 'databricks', 'spark', 'athena', 'clickhouse'] %}
      {{ dbt_data_engineering_toolkit.string_regex_extract_all("'a1b2'", '([0-9])', 1) }}
    {% else %}
      cast(null as {{ dbt.type_string() }})
    {% endif %} as regex_extract_all_value,
    {{ dbt_data_engineering_toolkit.string_remove_all_whitespace("' a b c '") }} as no_whitespace_value,
    {{ dbt_data_engineering_toolkit.string_rjust("'x'", 3, '_') }} as string_rjust_value,
    {{ dbt_data_engineering_toolkit.string_strip("'  stripped  '") }} as string_strip_value,
    {{ dbt_data_engineering_toolkit.string_upper("'upper'") }} as string_upper_value,
    {{ dbt_data_engineering_toolkit.try_cast("'42'", dbt.type_int()) }} as try_cast_value,
    {{ dbt_data_engineering_toolkit.winsorize('5', 0, 4) }} as winsorize_value,
    {% if target.type in ['duckdb', 'bigquery', 'athena', 'clickhouse'] %}
      {{ dbt_data_engineering_toolkit.unicode_normalize("'café'", 'NFC') }}
    {% else %}
      cast('café' as {{ dbt.type_string() }})
    {% endif %} as unicode_normalize_value
from source
