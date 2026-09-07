{% macro try_cast(expression, data_type) -%}
  {{ return(adapter.dispatch('try_cast', 'dbt_data_engineering_toolkit')(expression, data_type)) }}
{%- endmacro %}

{% macro default__try_cast(expression, data_type) -%}
  {{ exceptions.raise_compiler_error(
    "dbt_data_engineering_toolkit.try_cast is not implemented for adapter '" ~ target.type ~
    "'. A normal cast is intentionally not used because it can fail the model."
  ) }}
{%- endmacro %}

{% macro bigquery__try_cast(expression, data_type) -%}safe_cast({{ expression }} as {{ data_type }}){%- endmacro %}
{% macro snowflake__try_cast(expression, data_type) -%}try_cast({{ expression }} as {{ data_type }}){%- endmacro %}
{% macro duckdb__try_cast(expression, data_type) -%}try_cast({{ expression }} as {{ data_type }}){%- endmacro %}
{% macro databricks__try_cast(expression, data_type) -%}try_cast({{ expression }} as {{ data_type }}){%- endmacro %}
{% macro spark__try_cast(expression, data_type) -%}try_cast({{ expression }} as {{ data_type }}){%- endmacro %}
{% macro redshift__try_cast(expression, data_type) -%}try_cast({{ expression }} as {{ data_type }}){%- endmacro %}
{% macro athena__try_cast(expression, data_type) -%}try_cast({{ expression }} as {{ data_type }}){%- endmacro %}
{% macro clickhouse__try_cast(expression, data_type) -%}
  {% set normalized = data_type | string | trim %}
  {% set compact = normalized | lower | replace(' ', '') %}
  {% if compact[:8] == 'numeric(' %}
    {% set normalized = 'Decimal(' ~ compact[8:] %}
  {% endif %}
  accurateCastOrNull({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(normalized) }})
{%- endmacro %}

{% macro clean_integer(expression) -%}
  {{ return(dbt_data_engineering_toolkit.try_cast(dbt_data_engineering_toolkit.null_if_blank(expression), dbt.type_int())) }}
{%- endmacro %}

{% macro clean_numeric(expression, precision=38, scale=6) -%}
  {% if precision <= 0 or scale < 0 or scale > precision %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.clean_numeric requires precision > 0 and 0 <= scale <= precision.') }}
  {% endif %}
  {{ return(dbt_data_engineering_toolkit.try_cast(dbt_data_engineering_toolkit.null_if_blank(expression), 'numeric(' ~ precision ~ ', ' ~ scale ~ ')')) }}
{%- endmacro %}

{% macro clean_date(expression) -%}
  {{ return(dbt_data_engineering_toolkit.try_cast(dbt_data_engineering_toolkit.null_if_blank(expression), 'date')) }}
{%- endmacro %}

{% macro clean_timestamp(expression) -%}
  {{ return(dbt_data_engineering_toolkit.try_cast(dbt_data_engineering_toolkit.null_if_blank(expression), dbt.type_timestamp())) }}
{%- endmacro %}

{% macro clean_boolean(expression, true_values=['true', 't', 'yes', 'y', '1'], false_values=['false', 'f', 'no', 'n', '0']) -%}
  {% if true_values | length == 0 or false_values | length == 0 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.clean_boolean true_values and false_values cannot be empty.') }}
  {% endif %}
  {% set normalized %}lower(trim(cast({{ expression }} as {{ dbt.type_string() }}))){% endset %}
  case
    when {{ normalized }} in (
      {%- for value in true_values -%}
        {{ dbt_data_engineering_toolkit._det_sql_string(value | string | lower) }}{{ ', ' if not loop.last }}
      {%- endfor -%}
    ) then true
    when {{ normalized }} in (
      {%- for value in false_values -%}
        {{ dbt_data_engineering_toolkit._det_sql_string(value | string | lower) }}{{ ', ' if not loop.last }}
      {%- endfor -%}
    ) then false
    else null
  end
{%- endmacro %}
