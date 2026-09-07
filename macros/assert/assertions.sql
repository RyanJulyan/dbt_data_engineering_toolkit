{% macro assertions(column=none) -%}
  {% if column is none %}
    {{ return(dbt_assertions.assertions()) }}
  {% endif %}
  {{ return(dbt_assertions.assertions(column=column)) }}
{%- endmacro %}

{% macro assertions_filter(column=none, exclude_list=none, include_list=none, reverse=false) -%}
  {% set arguments = {'reverse': reverse} %}
  {% if column is not none %}{% do arguments.update({'column': column}) %}{% endif %}
  {% if exclude_list is not none %}{% do arguments.update({'exclude_list': exclude_list}) %}{% endif %}
  {% if include_list is not none %}{% do arguments.update({'include_list': include_list}) %}{% endif %}
  {{ return(dbt_assertions.assertions_filter(**arguments)) }}
{%- endmacro %}

{% macro keep_valid_rows(column=none) -%}
  {{ return(dbt_data_engineering_toolkit.assertions_filter(column=column, reverse=false)) }}
{%- endmacro %}

{% macro keep_quarantined_rows(column=none) -%}
  {{ return(dbt_data_engineering_toolkit.assertions_filter(column=column, reverse=true)) }}
{%- endmacro %}
