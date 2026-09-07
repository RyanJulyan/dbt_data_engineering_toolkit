with source as (
    select * from {{ ref('raw_key_value_mapping') }}
),

covered as (
    select
        id,
        {{ dbt_data_engineering_toolkit.clean_code(
            'status_code', corrections={'A': 'ACTIVE'}
        ) }} as clean_code_value,
        {{ dbt_data_engineering_toolkit.map_string(
            'status_code', {'A': 'active'}, default='unknown', case_sensitive=false, case='upper'
        ) }} as map_string_value,
        {{ dbt_data_engineering_toolkit.map_integer(
            'status_code', {'A': 10}, default=0, case_sensitive=false
        ) }} as map_integer_value,
        {{ dbt_data_engineering_toolkit.map_numeric(
            'amount_code', {'standard': '12.345'}, default=0, precision=18, scale=2
        ) }} as map_numeric_value,
        {{ dbt_data_engineering_toolkit.map_date(
            'date_code', {'launch': '2026-09-04'}, default='2026-01-01'
        ) }} as map_date_value,
        {{ dbt_data_engineering_toolkit.map_timestamp(
            'date_code', {'launch': '2026-09-04 12:30:00'}, default='2026-01-01 00:00:00'
        ) }} as map_timestamp_value,
        {{ dbt_data_engineering_toolkit.map_boolean(
            'flag_code', {'Y': 'yes'}, default=false, case_sensitive=false
        ) }} as map_boolean_value,
        {{ dbt_data_engineering_toolkit.key_value_map(
            'status_code', {'A': 'direct'}, default='other', data_type='string', case_sensitive=false
        ) }} as key_value_map_value,
        {{ dbt_data_engineering_toolkit.convert_value("'42'", 'integer') }} as convert_value_value,
        {{ dbt_data_engineering_toolkit.format_value(
            "'toolkit'", 'string', {'case': 'upper'}
        ) }} as format_value_value,
        {{ dbt_data_engineering_toolkit.format_number(
            "'1234.5'", decimal_places=2, grouping=true
        ) }} as format_number_value,
        {{ dbt_data_engineering_toolkit.format_temporal(
            dbt_data_engineering_toolkit.clean_date("'2026-09-04'"),
            'date',
            '%d/%m/%Y'
        ) }} as format_temporal_value,
        {{ dbt_data_engineering_toolkit.format_timestamp(
            dbt_data_engineering_toolkit.clean_timestamp("'2026-09-04 12:30:00'"),
            '%d/%m/%Y %H:%M'
        ) }} as format_timestamp_value
    from source
)

select * from covered
