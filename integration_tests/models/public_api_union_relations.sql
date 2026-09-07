{{ dbt_data_engineering_toolkit.union_relations(
    [ref('raw_customers'), ref('raw_customers')],
    include=['customer_id'],
    source_column_name=none
) }}
