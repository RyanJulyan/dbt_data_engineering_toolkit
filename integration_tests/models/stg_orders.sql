with cleaned as (
    select
        {{ dbt_data_engineering_toolkit.clean_string('order_id') }} as order_id,
        {{ dbt_data_engineering_toolkit.clean_numeric('subtotal', 18, 2) }} as subtotal,
        {{ dbt_data_engineering_toolkit.clean_numeric('tax', 18, 2) }} as tax,
        {{ dbt_data_engineering_toolkit.clean_numeric('discount', 18, 2) }} as discount,
        {{ dbt_data_engineering_toolkit.clean_numeric('total', 18, 2) }} as total,
        {{ dbt_data_engineering_toolkit.clean_date('start_date') }} as start_date,
        {{ dbt_data_engineering_toolkit.clean_date('end_date') }} as end_date,
        {{ dbt_data_engineering_toolkit.clean_string('status', case='lower') }} as status,
        {{ dbt_data_engineering_toolkit.clean_string('cancellation_reason') }} as cancellation_reason
    from {{ ref('raw_orders') }}
),

validated as (
    select
        *,
        {{ dbt_data_engineering_toolkit.rule_sum_equals(
            total='total',
            components=['subtotal', 'tax', '-discount'],
            tolerance=0.01
        ) }} as _total_reconciles,
        {{ dbt_data_engineering_toolkit.rule_date_order('start_date', 'end_date') }} as _date_order_valid,
        {{ dbt_data_engineering_toolkit.rule_required_when(
            'cancellation_reason',
            "status = 'cancelled'"
        ) }} as _cancellation_reason_valid
    from cleaned
)

select
    *,
    {{ dbt_data_engineering_toolkit.assertions() }}
from validated

