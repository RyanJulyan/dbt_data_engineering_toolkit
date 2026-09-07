with cleaned as (
    select
        {{ dbt_data_engineering_toolkit.clean_string('customer_id') }} as customer_id,
        {{ dbt_data_engineering_toolkit.clean_string('customer_name') }} as customer_name,
        {{ dbt_data_engineering_toolkit.clean_email('email') }} as email,
        {{ dbt_data_engineering_toolkit.clean_phone('phone') }} as phone,
        {{ dbt_data_engineering_toolkit.clean_boolean('active') }} as active,
        {{ dbt_data_engineering_toolkit.clean_numeric(
            'revenue', precision=18, scale=2
        ) }} as revenue,
        {{ dbt_data_engineering_toolkit.clean_date('signup_date') }} as signup_date,
        {{ dbt_data_engineering_toolkit.standardize_country(
            'country_code',
            aliases={'South Africa': 'ZA', 'United States': 'US'}
        ) }} as country_code
    from {{ ref('raw_customers') }}
),

validated as (
    select
        *,
        {{ dbt_data_engineering_toolkit.is_email('email') }} as _email_valid,
        {{ dbt_data_engineering_toolkit.is_positive(
            'revenue', allow_null=true
        ) }} as _revenue_valid
    from cleaned
)

select
    *,
    {{ dbt_data_engineering_toolkit.assertions() }},
    {{ dbt_data_engineering_toolkit.audit_columns('integration_test') }}
from validated
