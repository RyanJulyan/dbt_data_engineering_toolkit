select *
from {{ ref('stg_customers') }}
where {{ dbt_data_engineering_toolkit.keep_valid_rows() }}

