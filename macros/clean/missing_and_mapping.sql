{% macro fill_missing(expression, value) -%}
  coalesce({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_literal(value) }})
{%- endmacro %}

{% macro correct_errors(expression, correction_map) -%}
  {% do dbt_data_engineering_toolkit._det_assert_mapping(correction_map, 'correction_map') %}
  case
    {% for old, new in correction_map.items() %}
      {% if old is none %}
        when {{ expression }} is null then {{ dbt_data_engineering_toolkit._det_sql_literal(new) }}
      {% else %}
        when {{ expression }} = {{ dbt_data_engineering_toolkit._det_sql_literal(old) }} then {{ dbt_data_engineering_toolkit._det_sql_literal(new) }}
      {% endif %}
    {% endfor %}
    else {{ expression }}
  end
{%- endmacro %}

{% macro map_value(expression, mapping, default=none, preserve_unmapped=false, data_type=none, formatting=none, case_sensitive=true) -%}
  {% set mapping = dbt_data_engineering_toolkit._det_parse_mapping(mapping, 'mapping') %}
  {% if mapping | length == 0 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.map_value: mapping cannot be empty.') }}
  {% endif %}
  {% if formatting is not none and data_type is none %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.map_value: formatting requires data_type.') }}
  {% endif %}

  {% set source_key %}cast({{ expression }} as {{ dbt.type_string() }}){% endset %}
  {% if not case_sensitive %}{% set source_key %}lower({{ source_key }}){% endset %}{% endif %}

  {% set mapped_expression %}
    case
      {% for key, value in mapping.items() %}
        {% do dbt_data_engineering_toolkit._det_assert_scalar(key, 'mapping key') %}
        {% do dbt_data_engineering_toolkit._det_assert_scalar(value, "mapping value for '" ~ key ~ "'") %}
        {% if key is none %}
          when {{ expression }} is null then {{ dbt_data_engineering_toolkit.convert_value(dbt_data_engineering_toolkit._det_sql_literal(value), data_type) }}
        {% else %}
          {% set comparable_key = key | string if case_sensitive else key | string | lower %}
          when {{ source_key }} = {{ dbt_data_engineering_toolkit._det_sql_string(comparable_key) }}
            then {{ dbt_data_engineering_toolkit.convert_value(dbt_data_engineering_toolkit._det_sql_literal(value), data_type) }}
        {% endif %}
      {% endfor %}
      {% if preserve_unmapped %}
        else {{ dbt_data_engineering_toolkit.convert_value(expression, data_type) }}
      {% else %}
        {% do dbt_data_engineering_toolkit._det_assert_scalar(default, 'mapping default') %}
        else {{ dbt_data_engineering_toolkit.convert_value(dbt_data_engineering_toolkit._det_sql_literal(default), data_type) }}
      {% endif %}
    end
  {% endset %}

  {{ return(dbt_data_engineering_toolkit.format_value(mapped_expression, data_type, formatting)) }}
{%- endmacro %}

{% macro key_value_map(expression, mapping, default=none, preserve_unmapped=false, data_type=none, formatting=none, case_sensitive=true) -%}
  {{ return(dbt_data_engineering_toolkit.map_value(
      expression, mapping, default, preserve_unmapped, data_type, formatting, case_sensitive
  )) }}
{%- endmacro %}

{% macro label_encode(expression, categories, unknown=none) -%}
  {% do dbt_data_engineering_toolkit._det_assert_sequence(categories, 'categories') %}
  case
    {% for category in categories %}
      when {{ expression }} = {{ dbt_data_engineering_toolkit._det_sql_literal(category) }} then {{ loop.index0 }}
    {% endfor %}
    else {{ dbt_data_engineering_toolkit._det_sql_literal(unknown) }}
  end
{%- endmacro %}

{% macro one_hot(expression, categories, prefix='category') -%}
  {% do dbt_data_engineering_toolkit._det_assert_sequence(categories, 'categories') %}
  {% set columns = [] %}
  {% for category in categories %}
    {% set name = prefix ~ '_' ~ dbt_data_engineering_toolkit._det_slugify(category | string) %}
    {% set sql %}cast(case when {{ expression }} = {{ dbt_data_engineering_toolkit._det_sql_literal(category) }} then 1 else 0 end as {{ dbt.type_int() }}) as {{ adapter.quote(name) }}{% endset %}
    {% do columns.append(sql) %}
  {% endfor %}
  {{ return(columns | join(',\n    ')) }}
{%- endmacro %}

{% macro _det_string_position(haystack, needle) -%}
  {{ return(adapter.dispatch('_det_string_position', 'dbt_data_engineering_toolkit')(haystack, needle)) }}
{%- endmacro %}

{% macro default___det_string_position(haystack, needle) -%}
  position({{ needle }} in {{ haystack }})
{%- endmacro %}

{% macro bigquery___det_string_position(haystack, needle) -%}
  strpos({{ haystack }}, {{ needle }})
{%- endmacro %}

{% macro databricks___det_string_position(haystack, needle) -%}
  instr({{ haystack }}, {{ needle }})
{%- endmacro %}

{% macro spark___det_string_position(haystack, needle) -%}
  instr({{ haystack }}, {{ needle }})
{%- endmacro %}

{% macro athena___det_string_position(haystack, needle) -%}
  strpos({{ haystack }}, {{ needle }})
{%- endmacro %}

{% macro clickhouse___det_string_position(haystack, needle) -%}
  position({{ haystack }}, {{ needle }})
{%- endmacro %}

{% macro multi_hot(expression, categories, delimiter='|', prefix='token') -%}
  {% do dbt_data_engineering_toolkit._det_assert_sequence(categories, 'categories') %}
  {% if delimiter == '' %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.multi_hot: delimiter cannot be empty.') }}
  {% endif %}
  {% set columns = [] %}
  {% set delimiter_sql = dbt_data_engineering_toolkit._det_sql_string(delimiter) %}
  {% set haystack %}concat({{ delimiter_sql }}, cast({{ expression }} as {{ dbt.type_string() }}), {{ delimiter_sql }}){% endset %}
  {% for category in categories %}
    {% set name = prefix ~ '_' ~ dbt_data_engineering_toolkit._det_slugify(category | string) %}
    {% set needle = dbt_data_engineering_toolkit._det_sql_string(delimiter ~ category ~ delimiter) %}
    {% set sql %}cast(case when {{ dbt_data_engineering_toolkit._det_string_position(haystack, needle) }} > 0 then 1 else 0 end as {{ dbt.type_int() }}) as {{ adapter.quote(name) }}{% endset %}
    {% do columns.append(sql) %}
  {% endfor %}
  {{ return(columns | join(',\n    ')) }}
{%- endmacro %}
