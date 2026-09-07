{% macro _det_raise_invalid(name, value, allowed) -%}
  {{ exceptions.raise_compiler_error(
      "dbt_data_engineering_toolkit: invalid " ~ name ~ " '" ~ value ~
      "'. Allowed values: " ~ (allowed | join(', '))
  ) }}
{%- endmacro %}

{% macro _det_validate_choice(name, value, allowed) -%}
  {% if value not in allowed %}
    {{ dbt_data_engineering_toolkit._det_raise_invalid(name, value, allowed) }}
  {% endif %}
  {{ return(value) }}
{%- endmacro %}

{% macro _det_sql_string(value) -%}
  {{ return("'" ~ (value | string | replace("'", "''")) ~ "'") }}
{%- endmacro %}

{% macro _det_regex_string(value) -%}
  {{ return(adapter.dispatch('_det_regex_string', 'dbt_data_engineering_toolkit')(value)) }}
{%- endmacro %}

{% macro default___det_regex_string(value) -%}
  {{ return(dbt_data_engineering_toolkit._det_sql_string(value)) }}
{%- endmacro %}

{% macro snowflake___det_regex_string(value) -%}
  {% if '$$' in value | string %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit: Snowflake regex values cannot contain the dollar-quote delimiter $$') }}
  {% endif %}
  {{ return('$$' ~ value ~ '$$') }}
{%- endmacro %}

{% macro bigquery___det_regex_string(value) -%}
  {{ return('r' ~ dbt_data_engineering_toolkit._det_sql_string(value)) }}
{%- endmacro %}

{% macro databricks___det_regex_string(value) -%}
  {{ return('r' ~ dbt_data_engineering_toolkit._det_sql_string(value)) }}
{%- endmacro %}

{% macro spark___det_regex_string(value) -%}
  {{ return('r' ~ dbt_data_engineering_toolkit._det_sql_string(value)) }}
{%- endmacro %}

{% macro clickhouse___det_regex_string(value) -%}
  {% set escaped = value | string | replace('\\', '\\\\') %}
  {{ return(dbt_data_engineering_toolkit._det_sql_string(escaped)) }}
{%- endmacro %}

{% macro _det_sql_literal(value) -%}
  {% if value is none %}
    {{ return('null') }}
  {% elif value is boolean %}
    {{ return('true' if value else 'false') }}
  {% elif value is number %}
    {{ return(value | string) }}
  {% else %}
    {{ return(dbt_data_engineering_toolkit._det_sql_string(value)) }}
  {% endif %}
{%- endmacro %}

{% macro _det_assert_sequence(value, name='value') -%}
  {% if value is string or value is mapping or value is not iterable %}
    {{ exceptions.raise_compiler_error(
      "dbt_data_engineering_toolkit: " ~ name ~ " must be a list/sequence."
    ) }}
  {% endif %}
  {{ return(value) }}
{%- endmacro %}

{% macro _det_assert_mapping(value, name='mapping') -%}
  {% if value is not mapping %}
    {{ exceptions.raise_compiler_error(
      "dbt_data_engineering_toolkit: " ~ name ~ " must be a dictionary/mapping."
    ) }}
  {% endif %}
  {{ return(value) }}
{%- endmacro %}

{% macro _det_parse_mapping(value, name='mapping') -%}
  {% if value is string %}
    {% set value = fromjson(value) %}
  {% endif %}
  {% do dbt_data_engineering_toolkit._det_assert_mapping(value, name) %}
  {{ return(value) }}
{%- endmacro %}

{% macro _det_assert_scalar(value, name='value') -%}
  {% if value is mapping or (value is iterable and value is not string) %}
    {{ exceptions.raise_compiler_error(
      "dbt_data_engineering_toolkit: " ~ name ~ " must be a scalar JSON value."
    ) }}
  {% endif %}
  {{ return(value) }}
{%- endmacro %}

{% macro _det_required(mapping, key, context='configuration') -%}
  {% if key not in mapping %}
    {{ exceptions.raise_compiler_error(
      "dbt_data_engineering_toolkit: " ~ context ~ " requires '" ~ key ~ "'."
    ) }}
  {% endif %}
  {{ return(mapping[key]) }}
{%- endmacro %}
