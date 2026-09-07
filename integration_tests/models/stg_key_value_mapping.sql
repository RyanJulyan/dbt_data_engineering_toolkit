with mapped as (
    select
        {{ dbt_data_engineering_toolkit.clean_integer('id') }} as id,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='status_code',
            mapping='{"A":"Active","I":"Inactive"}',
            default='Unknown',
            data_type='string',
            format={'case': 'upper'},
            case_sensitive=false
        ) }} as status_label,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='amount_code',
            mapping={
                'standard': '1234.5',
                'premium': '98765.432',
                'unknown': 'not-a-number'
            },
            default=0,
            data_type={'name': 'numeric', 'precision': 18, 'scale': 2}
        ) }} as amount_value,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='amount_code',
            mapping={
                'standard': '1234.5',
                'premium': '98765.432',
                'unknown': 'not-a-number'
            },
            default=0,
            data_type={'name': 'numeric', 'precision': 18, 'scale': 2},
            format={
                'decimal_places': 2,
                'grouping': true,
                'prefix': 'R ',
                'null_value': 'INVALID'
            }
        ) }} as amount_display,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='date_code',
            mapping={
                'launch': '2026-09-04',
                'renewal': '2027-01-15',
                'unknown': 'not-a-date'
            },
            default='2026-01-01',
            data_type='date'
        ) }} as event_date,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='date_code',
            mapping={
                'launch': '2026-09-04',
                'renewal': '2027-01-15',
                'unknown': 'not-a-date'
            },
            default='2026-01-01',
            data_type='date',
            format={'pattern': '%d/%m/%Y', 'null_value': 'INVALID DATE'}
        ) }} as event_date_display,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='flag_code',
            mapping={'Y': 'yes', 'N': 'no'},
            default=false,
            data_type='boolean',
            case_sensitive=false
        ) }} as enabled,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='status_code',
            mapping={'A': '10', 'I': '20'},
            default=0,
            data_type='integer',
            case_sensitive=false
        ) }} as status_rank,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='date_code',
            mapping={
                'launch': '2026-09-04 12:30:00',
                'renewal': '2027-01-15 08:00:00',
                'unknown': 'not-a-timestamp'
            },
            default='2026-01-01 00:00:00',
            data_type='timestamp'
        ) }} as event_at,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='date_code',
            mapping={
                'launch': '2026-09-04 12:30:00',
                'renewal': '2027-01-15 08:00:00',
                'unknown': 'not-a-timestamp'
            },
            default='2026-01-01 00:00:00',
            data_type='timestamp',
            format={
                'pattern': '%d/%m/%Y %H:%M',
                'null_value': 'INVALID TIMESTAMP'
            }
        ) }} as event_at_display,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='status_code',
            mapping={'A': 'Active'},
            data_type='string'
        ) }} as explicit_null_default,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='status_code',
            mapping={'A': 'Active'},
            preserve_unmapped=true,
            data_type='string'
        ) }} as status_preserved,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='amount_code',
            mapping={
                'standard': '1234.5',
                'premium': '98765.432',
                'unknown': 'not-a-number'
            },
            default=0,
            data_type={'name': 'numeric', 'precision': 18, 'scale': 2},
            format={
                'decimal_places': 2,
                'grouping': true,
                'prefix': 'R ',
                'null_value': 'INVALID'
            }
        ) }} as amount_display_operation,
        {{ dbt_data_engineering_toolkit.format_date(
            dbt_data_engineering_toolkit.clean_date("'2026-12-31'"),
            pattern='%d %b %Y'
        ) }} as converted_date_operation
    from {{ ref('raw_key_value_mapping') }}
)

select
    *,
    {{ dbt_data_engineering_toolkit.format_string(
        'status_label', case='title'
    ) }} as status_title
from mapped
