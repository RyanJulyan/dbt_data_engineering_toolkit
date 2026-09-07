{% macro normalize_whitespace(expression) -%}
  {{ return(adapter.dispatch('normalize_whitespace', 'dbt_data_engineering_toolkit')(expression)) }}
{%- endmacro %}

{% macro default__normalize_whitespace(expression) -%}
  regexp_replace({{ expression }}, '[[:space:]]+', ' ')
{%- endmacro %}

{% macro bigquery__normalize_whitespace(expression) -%}
  regexp_replace({{ expression }}, r'\s+', ' ')
{%- endmacro %}

{% macro postgres__normalize_whitespace(expression) -%}
  regexp_replace({{ expression }}, '[[:space:]]+', ' ', 'g')
{%- endmacro %}

{% macro redshift__normalize_whitespace(expression) -%}
  regexp_replace({{ expression }}, '[[:space:]]+', ' ', 1, 0, 'p')
{%- endmacro %}

{% macro duckdb__normalize_whitespace(expression) -%}
  regexp_replace({{ expression }}, '\s+', ' ', 'g')
{%- endmacro %}

{% macro clickhouse__normalize_whitespace(expression) -%}
  replaceRegexpAll({{ expression }}, '\\s+', ' ')
{%- endmacro %}

{% macro null_if_blank(expression) -%}
  nullif(trim(cast({{ expression }} as {{ dbt.type_string() }})), '')
{%- endmacro %}

{% macro clean_string(expression, trim=true, collapse_whitespace=true, case='preserve', blank_as_null=true) -%}
  {% set allowed_cases = ['preserve', 'lower', 'upper'] %}
  {% set case = dbt_data_engineering_toolkit._det_validate_choice('case', case, allowed_cases) %}
  {% set result %}cast({{ expression }} as {{ dbt.type_string() }}){% endset %}
  {% if trim %}{% set result %}trim({{ result }}){% endset %}{% endif %}
  {% if collapse_whitespace %}{% set result %}{{ dbt_data_engineering_toolkit.normalize_whitespace(result) }}{% endset %}{% endif %}
  {% if case == 'lower' %}{% set result %}lower({{ result }}){% endset %}{% endif %}
  {% if case == 'upper' %}{% set result %}upper({{ result }}){% endset %}{% endif %}
  {% if blank_as_null %}{% set result %}nullif({{ result }}, ''){% endset %}{% endif %}
  {{ return(result) }}
{%- endmacro %}

{% macro clean_email(expression) -%}
  {{ return(dbt_data_engineering_toolkit.clean_string(expression, case='lower')) }}
{%- endmacro %}

{% macro regex_replace_all(expression, pattern, replacement='') -%}
  {{ return(adapter.dispatch('regex_replace_all', 'dbt_data_engineering_toolkit')(expression, pattern, replacement)) }}
{%- endmacro %}

{% macro default__regex_replace_all(expression, pattern, replacement='') -%}
  regexp_replace({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ dbt_data_engineering_toolkit._det_regex_string(replacement) }})
{%- endmacro %}

{% macro postgres__regex_replace_all(expression, pattern, replacement='') -%}
  regexp_replace({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ dbt_data_engineering_toolkit._det_regex_string(replacement) }}, 'g')
{%- endmacro %}

{% macro duckdb__regex_replace_all(expression, pattern, replacement='') -%}
  regexp_replace({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ dbt_data_engineering_toolkit._det_regex_string(replacement) }}, 'g')
{%- endmacro %}

{% macro bigquery__regex_replace_all(expression, pattern, replacement='') -%}
  regexp_replace({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ dbt_data_engineering_toolkit._det_regex_string(replacement) }})
{%- endmacro %}

{% macro clickhouse__regex_replace_all(expression, pattern, replacement='') -%}
  replaceRegexpAll({{ expression }}, {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ dbt_data_engineering_toolkit._det_regex_string(replacement) }})
{%- endmacro %}

{% macro clean_phone(expression, keep_plus=true) -%}
  {% set source = dbt_data_engineering_toolkit.null_if_blank(expression) %}
  {% set pattern = '[^0-9+]' if keep_plus else '[^0-9]' %}
  nullif({{ dbt_data_engineering_toolkit.regex_replace_all(source, pattern, '') }}, '')
{%- endmacro %}
