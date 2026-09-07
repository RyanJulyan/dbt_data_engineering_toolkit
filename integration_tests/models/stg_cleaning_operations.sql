with distinct_source as (
    {{ dbt_data_engineering_toolkit.distinct_rows(ref('raw_cleaning_operations')) }}
),

cleaned as (
    select
        {{ dbt_data_engineering_toolkit.clean_integer('id') }} as id,
        {{ dbt_data_engineering_toolkit.clean_string('raw_text') }} as cleaned_text,
        {{ dbt_data_engineering_toolkit.correct_errors(
            'code', {'ERR': 'OK', 'legacy': 'CURRENT'}
        ) }} as corrected_code,
        {{ dbt_data_engineering_toolkit.label_encode(
            'category', ['alpha', 'beta'], unknown=-1
        ) }} as category_label,
        {{ dbt_data_engineering_toolkit.clean_numeric('amount') }} as amount,
        category,
        tags,
        signed_number,
        code
    from distinct_source
),

without_affixes as (
    select
        *,
        {{ dbt_data_engineering_toolkit.string_remove_suffix(
            dbt_data_engineering_toolkit.string_remove_prefix(
                'cleaned_text', 'PRE_'
            ),
            '_suf'
        ) }} as text_without_affixes
    from cleaned
),

transformed as (
    select
        id,
        {{ dbt_data_engineering_toolkit.string_remove_punctuation(
            dbt_data_engineering_toolkit.string_lower('text_without_affixes')
        ) }} as cleaned_text,
        corrected_code,
        category_label,
        {{ dbt_data_engineering_toolkit.fill_missing('amount', 0) }} as amount_filled,
        {{ dbt_data_engineering_toolkit.clip('amount', 0, 100) }} as amount_clipped,
        {{ dbt_data_engineering_toolkit.min_max_scale('amount') }} as amount_scaled,
        category,
        tags,
        signed_number,
        code,
        amount
    from without_affixes
)

select
    id,
    cleaned_text,
    corrected_code,
    category_label,
    amount_filled,
    amount_clipped,
    amount_scaled,
    {{ dbt_data_engineering_toolkit.one_hot(
        'category', ['alpha', 'beta'], 'category'
    ) }},
    {{ dbt_data_engineering_toolkit.multi_hot(
        'tags', ['red', 'blue', 'gold'], '|', 'tag'
    ) }},
    {{ dbt_data_engineering_toolkit.string_split_part(
        'tags', '|', 2
    ) }} as second_tag,
    {{ dbt_data_engineering_toolkit.string_zfill(
        'signed_number', 5
    ) }} as padded_number,
    {{ dbt_data_engineering_toolkit.string_slice(
        'code', 0, 2
    ) }} as code_slice,
    {{ dbt_data_engineering_toolkit.string_slice_replace(
        'code', 0, 1, 'X'
    ) }} as code_replaced,
    {{ dbt_data_engineering_toolkit.bin_numeric(
        'amount',
        [-10, 0, 50, 250],
        ['low', 'medium', 'high'],
        include_lowest=true
    ) }} as amount_band,
    {{ dbt_data_engineering_toolkit.is_zscore_anomaly(
        'amount', 1.4
    ) }} as amount_zscore_anomaly
from transformed
