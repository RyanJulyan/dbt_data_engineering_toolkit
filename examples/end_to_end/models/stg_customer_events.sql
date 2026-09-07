with distinct_source as (
    {{ dbt_data_engineering_toolkit.distinct_rows(ref('raw_customer_events')) }}
),

cleaned as (
    select
        {{ dbt_data_engineering_toolkit.clean_string('customer_id') }} as customer_id,
        {{ de_toolkit.clean_string('customer_name') }} as customer_name,
        {{ dbt_data_engineering_toolkit.clean_email('email') }} as email,
        {{ dbt_data_engineering_toolkit.clean_phone('phone') }} as phone,
        {{ dbt_data_engineering_toolkit.clean_boolean('active') }} as active,
        {{ dbt_data_engineering_toolkit.clean_numeric(
            'revenue', precision=18, scale=2
        ) }} as revenue,
        {{ dbt_data_engineering_toolkit.clean_date('signup_date') }} as signup_date,
        {{ dbt_data_engineering_toolkit.standardize_country(
            'country',
            aliases={'South Africa': 'ZA', 'United States': 'US'}
        ) }} as country_code,
        status_code,
        price_band,
        event_code,
        {{ dbt_data_engineering_toolkit.clean_code(
            'account_code',
            remove_prefix='legacy_',
            corrections={'UK': 'GB'}
        ) }} as account_code
    from distinct_source
),

mapped as (
    select
        customer_id,
        customer_name,
        email,
        phone,
        active,
        revenue,
        signup_date,
        country_code,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='status_code',
            mapping='{"A":"active","I":"inactive"}',
            default='unknown',
            data_type='string',
            format={'case': 'upper'},
            case_sensitive=false
        ) }} as status_label,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='price_band',
            mapping={
                'standard': '1234.5',
                'premium': '98765.432',
                'unknown': 'not-a-number'
            },
            default=0,
            data_type={'name': 'numeric', 'precision': 18, 'scale': 2}
        ) }} as price_amount,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='price_band',
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
        ) }} as price_display,
        {{ de_toolkit.mapping(
            expression='event_code',
            mapping={
                'launch': '2026-09-04',
                'renewal': '2027-01-15',
                'review': '2026-07-20'
            },
            data_type='date'
        ) }} as event_date,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='event_code',
            mapping={
                'launch': '2026-09-04',
                'renewal': '2027-01-15',
                'review': '2026-07-20'
            },
            default='2026-01-01',
            data_type='date',
            format={
                'pattern': '%d/%m/%Y',
                'null_value': 'UNKNOWN DATE'
            }
        ) }} as event_date_display,
        account_code
    from cleaned
),

validated as (
    select
        *,
        {{ dbt_data_engineering_toolkit.is_email('email') }} as _email_valid,
        {{ dbt_data_engineering_toolkit.is_positive(
            'revenue', allow_null=true
        ) }} as _revenue_valid,
        {{ dbt_data_engineering_toolkit.rule_compare(
            'signup_date', '<=', 'current_date', allow_null=false
        ) }} as _signup_date_valid
    from mapped
)

select
    *,
    {{ dbt_data_engineering_toolkit.assertions() }},
    {{ dbt_data_engineering_toolkit.audit_columns('demo_seed') }}
from validated
