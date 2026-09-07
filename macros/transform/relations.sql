{% macro drop_missing_rows(relation, columns) -%}
  {% do dbt_data_engineering_toolkit._det_assert_sequence(columns, 'columns') %}
  {% if columns | length == 0 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.drop_missing_rows: columns cannot be empty.') }}
  {% endif %}
  select *
  from {{ relation }}
  where
    {% for column in columns %}
      {{ adapter.quote(column) }} is not null{% if not loop.last %} and{% endif %}
    {% endfor %}
{%- endmacro %}

{% macro distinct_rows(relation) -%}
  select distinct * from {{ relation }}
{%- endmacro %}

{% macro trim_rows(relation, order_by, start_row=0, end_row=none) -%}
  {% if start_row < 0 or (end_row is not none and end_row < start_row) %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.trim_rows: require 0 <= start_row <= end_row.') }}
  {% endif %}
  with numbered as (
    select
      *,
      row_number() over (order by {{ order_by }}) as _det_row_number
    from {{ relation }}
  )
  select {{ dbt_data_engineering_toolkit._det_star(from=relation, relation_alias='numbered') }}
  from numbered
  where _det_row_number > {{ start_row }}
    {% if end_row is not none %}and _det_row_number <= {{ end_row }}{% endif %}
{%- endmacro %}

{% macro undersample_classes(relation, target_column, order_by) -%}
  with class_counts as (
    select {{ target_column }} as _det_class, count(*) as _det_class_count
    from {{ relation }}
    group by 1
  ),
  minimum_count as (
    select min(_det_class_count) as _det_keep_count from class_counts
  ),
  ranked as (
    select
      source_data.*,
      row_number() over (partition by {{ target_column }} order by {{ order_by }}) as _det_class_row
    from {{ relation }} as source_data
  )
  select {{ dbt_data_engineering_toolkit._det_star(from=relation, relation_alias='ranked') }}
  from ranked
  cross join minimum_count
  where _det_class_row <= _det_keep_count
{%- endmacro %}
