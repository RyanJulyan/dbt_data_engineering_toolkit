with compared as (
    select
        {{ dbt_data_engineering_toolkit.clean_string('customer_id') }} as customer_id,
        {{ dbt_data_engineering_toolkit.clean_string('customer_name') }} as canonical_name,
        {{ de_toolkit.clean_string('customer_name') }} as aliased_name,
        {{ dbt_data_engineering_toolkit.mapping(
            expression='active',
            mapping={'YES': 'active', 'no': 'inactive'},
            default='unknown',
            data_type='string',
            format={'case': 'upper'},
            case_sensitive=false
        ) }} as canonical_status,
        {{ de_toolkit.mapping(
            expression='active',
            mapping={'YES': 'active', 'no': 'inactive'},
            default='unknown',
            data_type='string',
            format={'case': 'upper'},
            case_sensitive=false
        ) }} as aliased_status,
        {{ dbt_data_engineering_toolkit.surrogate_key(
            ['customer_id', 'customer_name']
        ) }} as canonical_surrogate_key,
        {{ de_toolkit.surrogate_key(
            ['customer_id', 'customer_name']
        ) }} as aliased_surrogate_key
    from {{ ref('raw_customers') }}
),

validated as (
    select
        *,
        canonical_name is not distinct from aliased_name
            and canonical_status is not distinct from aliased_status
            and canonical_surrogate_key is not distinct from aliased_surrogate_key
            as _namespaces_match
    from compared
)

select
    *,
    {{ de_toolkit.assertions() }}
from validated
