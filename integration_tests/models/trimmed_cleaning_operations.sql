{{ dbt_data_engineering_toolkit.trim_rows(ref('raw_cleaning_operations'), 'id, raw_text', 1, 3) }}
