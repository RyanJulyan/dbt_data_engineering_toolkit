{% macro mapping(expression, mapping, default=none, preserve_unmapped=false, data_type=none, format=none, case_sensitive=true) -%}
  {#
    Public inline mapping API: one source SQL expression in, one mapped SQL
    expression out. Optional conversion happens before optional formatting.
  #}
  {{ return(dbt_data_engineering_toolkit.map_value(
      expression,
      mapping,
      default,
      preserve_unmapped,
      data_type,
      format,
      case_sensitive
  )) }}
{%- endmacro %}
