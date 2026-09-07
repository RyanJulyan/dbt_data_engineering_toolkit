{#
  Inline-first mapping and formatting helpers.

  These macros intentionally accept one SQL expression and return one SQL
  expression. They keep transformation logic beside the selected column and
  avoid requiring a separate configuration dictionary.
#}

{% macro map_string(expression, mapping, default=none, preserve_unmapped=false, case_sensitive=true, case='preserve', trim=false, collapse_whitespace=false, blank_as_null=false) -%}
  {% set formatting = {
      'case': case,
      'trim': trim,
      'collapse_whitespace': collapse_whitespace,
      'blank_as_null': blank_as_null
  } %}
  {{ return(dbt_data_engineering_toolkit.key_value_map(
      expression,
      mapping,
      default,
      preserve_unmapped,
      'string',
      formatting,
      case_sensitive
  )) }}
{%- endmacro %}

{% macro map_integer(expression, mapping, default=none, preserve_unmapped=false, case_sensitive=true) -%}
  {{ return(dbt_data_engineering_toolkit.key_value_map(
      expression,
      mapping,
      default,
      preserve_unmapped,
      'integer',
      none,
      case_sensitive
  )) }}
{%- endmacro %}

{% macro map_numeric(expression, mapping, default=none, preserve_unmapped=false, case_sensitive=true, precision=38, scale=6) -%}
  {{ return(dbt_data_engineering_toolkit.key_value_map(
      expression,
      mapping,
      default,
      preserve_unmapped,
      {'name': 'numeric', 'precision': precision, 'scale': scale},
      none,
      case_sensitive
  )) }}
{%- endmacro %}

{% macro map_date(expression, mapping, default=none, preserve_unmapped=false, case_sensitive=true) -%}
  {{ return(dbt_data_engineering_toolkit.key_value_map(
      expression,
      mapping,
      default,
      preserve_unmapped,
      'date',
      none,
      case_sensitive
  )) }}
{%- endmacro %}

{% macro map_timestamp(expression, mapping, default=none, preserve_unmapped=false, case_sensitive=true) -%}
  {{ return(dbt_data_engineering_toolkit.key_value_map(
      expression,
      mapping,
      default,
      preserve_unmapped,
      'timestamp',
      none,
      case_sensitive
  )) }}
{%- endmacro %}

{% macro map_boolean(expression, mapping, default=none, preserve_unmapped=false, case_sensitive=true, true_values=['true', 't', 'yes', 'y', '1'], false_values=['false', 'f', 'no', 'n', '0']) -%}
  {{ return(dbt_data_engineering_toolkit.key_value_map(
      expression,
      mapping,
      default,
      preserve_unmapped,
      {
          'name': 'boolean',
          'true_values': true_values,
          'false_values': false_values
      },
      none,
      case_sensitive
  )) }}
{%- endmacro %}

{% macro format_string(expression, case='preserve', trim=false, collapse_whitespace=false, blank_as_null=false, null_value=none) -%}
  {% set result = dbt_data_engineering_toolkit.clean_string(
      expression,
      trim,
      collapse_whitespace,
      case if case in ['preserve', 'lower', 'upper'] else 'preserve',
      blank_as_null
  ) %}
  {% do dbt_data_engineering_toolkit._det_validate_choice(
      'string format case', case,
      ['preserve', 'lower', 'upper', 'title', 'capitalize']
  ) %}
  {% if case == 'title' %}
    {% set result = dbt_data_engineering_toolkit.string_title(result) %}
  {% elif case == 'capitalize' %}
    {% set result = dbt_data_engineering_toolkit.string_capitalize(result) %}
  {% endif %}
  {% if null_value is not none %}
    {% set result %}coalesce({{ result }}, {{ dbt_data_engineering_toolkit._det_sql_string(null_value) }}){% endset %}
  {% endif %}
  {{ return(result) }}
{%- endmacro %}

{% macro format_date(expression, pattern='%Y-%m-%d', null_value=none) -%}
  {% set result = dbt_data_engineering_toolkit.format_temporal(expression, 'date', pattern) %}
  {% if null_value is not none %}
    {% set result %}coalesce({{ result }}, {{ dbt_data_engineering_toolkit._det_sql_string(null_value) }}){% endset %}
  {% endif %}
  {{ return(result) }}
{%- endmacro %}

{% macro format_timestamp(expression, pattern='%Y-%m-%d %H:%M:%S', null_value=none) -%}
  {% set result = dbt_data_engineering_toolkit.format_temporal(expression, 'timestamp', pattern) %}
  {% if null_value is not none %}
    {% set result %}coalesce({{ result }}, {{ dbt_data_engineering_toolkit._det_sql_string(null_value) }}){% endset %}
  {% endif %}
  {{ return(result) }}
{%- endmacro %}

{% macro clean_code(expression, remove_prefix=none, remove_suffix=none, case='upper', corrections={}, blank_as_null=true) -%}
  {% do dbt_data_engineering_toolkit._det_validate_choice(
      'code case', case, ['preserve', 'lower', 'upper']
  ) %}
  {% do dbt_data_engineering_toolkit._det_assert_mapping(corrections, 'corrections') %}

  {% set result = dbt_data_engineering_toolkit.clean_string(
      expression,
      trim=true,
      collapse_whitespace=true,
      case='preserve',
      blank_as_null=blank_as_null
  ) %}
  {% if remove_prefix is not none %}
    {% set result = dbt_data_engineering_toolkit.string_remove_prefix(result, remove_prefix) %}
  {% endif %}
  {% if remove_suffix is not none %}
    {% set result = dbt_data_engineering_toolkit.string_remove_suffix(result, remove_suffix) %}
  {% endif %}
  {% if case == 'lower' %}
    {% set result = dbt_data_engineering_toolkit.string_lower(result) %}
  {% elif case == 'upper' %}
    {% set result = dbt_data_engineering_toolkit.string_upper(result) %}
  {% endif %}
  {% if corrections | length > 0 %}
    {% set result = dbt_data_engineering_toolkit.correct_errors(result, corrections) %}
  {% endif %}
  {{ return(result) }}
{%- endmacro %}
