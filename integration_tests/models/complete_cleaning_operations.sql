{{ dbt_data_engineering_toolkit.drop_missing_rows(ref('raw_cleaning_operations'), ['amount', 'category']) }}
