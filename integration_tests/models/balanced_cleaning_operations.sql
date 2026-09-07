{{ dbt_data_engineering_toolkit.undersample_classes(ref('raw_cleaning_operations'), 'category', 'id, raw_text') }}
