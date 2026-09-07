select *
from {{ ref('public_api_coverage') }}
where id = 1
  and (
    clean_code_value <> 'ACTIVE'
    or map_string_value <> 'ACTIVE'
    or map_integer_value <> 10
    or map_numeric_value <> 12.35
    or map_date_value <> cast('2026-09-04' as date)
    or map_timestamp_value <> cast('2026-09-04 12:30:00' as {{ dbt.type_timestamp() }})
    or map_boolean_value is not true
    or key_value_map_value <> 'direct'
    or convert_value_value <> 42
    or format_value_value <> 'TOOLKIT'
    or format_number_value <> '1,234.50'
    or format_temporal_value <> '04/09/2026'
    or format_timestamp_value <> '04/09/2026 12:30'
  )
