{% macro standardize_code(expression, aliases={}, length=none) -%}
  {% do dbt_data_engineering_toolkit._det_assert_mapping(aliases, 'aliases') %}
  {% set normalized %}upper({{ dbt_data_engineering_toolkit.clean_string(expression, case='preserve') }}){% endset %}
  case
    {% for alias, code in aliases.items() %}
    when {{ normalized }} = upper({{ dbt_data_engineering_toolkit._det_sql_string(alias) }}) then {{ dbt_data_engineering_toolkit._det_sql_string(code | upper) }}
    {% endfor %}
    {% if length is not none %}
    when length({{ normalized }}) = {{ length }} then {{ normalized }}
    else null
    {% else %}
    else {{ normalized }}
    {% endif %}
  end
{%- endmacro %}

{% macro standardize_country(expression, aliases={}) -%}
  {{ return(dbt_data_engineering_toolkit.standardize_code(expression, aliases, 2)) }}
{%- endmacro %}

{% macro standardize_currency(expression, aliases={}) -%}
  {{ return(dbt_data_engineering_toolkit.standardize_code(expression, aliases, 3)) }}
{%- endmacro %}

