{% macro regex_match(expression, pattern) -%}
  {{ return(adapter.dispatch('regex_match', 'dbt_data_engineering_toolkit')(expression, pattern)) }}
{%- endmacro %}

{% macro default__regex_match(expression, pattern) -%}regexp_like({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro bigquery__regex_match(expression, pattern) -%}regexp_contains({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro postgres__regex_match(expression, pattern) -%}({{ expression }} ~ {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro redshift__regex_match(expression, pattern) -%}({{ expression }} ~ {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro snowflake__regex_match(expression, pattern) -%}regexp_like({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro duckdb__regex_match(expression, pattern) -%}regexp_matches({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro databricks__regex_match(expression, pattern) -%}({{ expression }} rlike {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro spark__regex_match(expression, pattern) -%}({{ expression }} rlike {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro athena__regex_match(expression, pattern) -%}regexp_like({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}
{% macro clickhouse__regex_match(expression, pattern) -%}match(toString({{ expression }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}){%- endmacro %}

{% macro is_email(expression, allow_null=false) -%}
  (case
    when {{ expression }} is null then {{ 'true' if allow_null else 'false' }}
    else {{ dbt_data_engineering_toolkit.regex_match(expression, '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$') }}
  end)
{%- endmacro %}

{% macro is_positive(expression, allow_null=false) -%}
  (case when {{ expression }} is null then {{ 'true' if allow_null else 'false' }} else {{ expression }} > 0 end)
{%- endmacro %}

{% macro is_between(expression, min_value=none, max_value=none, inclusive=true, allow_null=false) -%}
  {% if min_value is none and max_value is none %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.is_between requires min_value, max_value, or both.') }}
  {% endif %}
  (case when {{ expression }} is null then {{ 'true' if allow_null else 'false' }} else
    {% if min_value is not none %}{{ expression }} {{ '>=' if inclusive else '>' }} {{ min_value }}{% endif %}
    {% if min_value is not none and max_value is not none %} and {% endif %}
    {% if max_value is not none %}{{ expression }} {{ '<=' if inclusive else '<' }} {{ max_value }}{% endif %}
  end)
{%- endmacro %}

{% macro is_in_list(expression, values, allow_null=false, case_sensitive=true) -%}
  {% if values | length == 0 %}{{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.is_in_list values cannot be empty.') }}{% endif %}
  {% set lhs = expression if case_sensitive else 'lower(' ~ expression ~ ')' %}
  (case when {{ expression }} is null then {{ 'true' if allow_null else 'false' }} else
    {{ lhs }} in (
      {%- for value in values -%}
        {{ dbt_data_engineering_toolkit._det_sql_string(value if case_sensitive else value | lower) }}{{ ', ' if not loop.last }}
      {%- endfor -%}
    )
  end)
{%- endmacro %}
