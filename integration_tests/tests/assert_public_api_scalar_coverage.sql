select *
from {{ ref('public_api_scalar_coverage') }}
where id = '1'
  and (
    not assertions_filter_value
    or not is_between_value
    or not is_in_list_value
    or map_value_value <> 'active'
    or mask_hash_value is null
    or mask_redact_value <> '[REDACTED]'
    or normalized_value <> ' hello world '
    or blank_value is not null
    or not regex_match_value
    or regex_replace_value <> 'ab'
    or not rule_compare_value
    or not rule_one_of_value
    or safe_add_value <> 3
    or safe_divide_value <> 2
    or safe_subtract_value <> -1
    or standardize_code_value <> 'UK'
    or standardize_currency_value <> 'ZAR'
    or string_casefold_value <> 'abc'
    or string_center_value <> '_x_'
    or string_ljust_value <> 'x__'
    {% if target.type in ['duckdb', 'bigquery', 'snowflake', 'databricks', 'spark', 'athena', 'clickhouse'] %}
      or regex_extract_all_value is null
    {% endif %}
    or no_whitespace_value <> 'abc'
    or string_rjust_value <> '__x'
    or string_strip_value <> 'stripped'
    or string_upper_value <> 'UPPER'
    or try_cast_value <> 42
    or winsorize_value <> 4
    or unicode_normalize_value <> 'café'
  )
