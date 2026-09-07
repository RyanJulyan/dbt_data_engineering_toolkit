select *
from {{ ref('stg_customer_events') }}
where {{ dbt_data_engineering_toolkit.keep_valid_rows() }}
