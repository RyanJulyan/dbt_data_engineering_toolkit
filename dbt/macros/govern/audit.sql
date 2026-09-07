{% macro audit_columns(source_system=none, loaded_at_expression=none, prefix='_det_') -%}
  {% set configured_source = var('dbt_data_engineering_toolkit', {}).get('audit_source_system') %}
  {% set source_system = source_system if source_system is not none else configured_source %}
  {% set loaded_at_expression = loaded_at_expression if loaded_at_expression is not none else dbt.current_timestamp() %}
  {{ loaded_at_expression }} as {{ adapter.quote(prefix ~ 'loaded_at') }},
  {{ dbt_data_engineering_toolkit._det_sql_string(invocation_id) }} as {{ adapter.quote(prefix ~ 'invocation_id') }}
  {% if source_system is not none %},
  {{ dbt_data_engineering_toolkit._det_sql_string(source_system) }} as {{ adapter.quote(prefix ~ 'source_system') }}
  {% endif %}
{%- endmacro %}

{% macro mask_hash(expression, salt_expression=none) -%}
  {% set fields = [expression] %}
  {% if salt_expression is not none %}{% do fields.append(salt_expression) %}{% endif %}
  {{ return(dbt_data_engineering_toolkit.surrogate_key(fields)) }}
{%- endmacro %}

{% macro mask_redact(expression, replacement='[REDACTED]', preserve_null=true) -%}
  {% if preserve_null %}case when {{ expression }} is null then null else {{ dbt_data_engineering_toolkit._det_sql_string(replacement) }} end
  {% else %}{{ dbt_data_engineering_toolkit._det_sql_string(replacement) }}{% endif %}
{%- endmacro %}
