{% macro rule_compare(left, operator, right, allow_null=false) -%}
  {% set operator = dbt_data_engineering_toolkit._det_validate_choice('operator', operator, ['=', '!=', '<>', '<', '<=', '>', '>=']) %}
  (case when {{ left }} is null or {{ right }} is null then {{ 'true' if allow_null else 'false' }} else {{ left }} {{ operator }} {{ right }} end)
{%- endmacro %}

{% macro rule_date_order(start_date, end_date, allow_null=false) -%}
  {{ return(dbt_data_engineering_toolkit.rule_compare(start_date, '<=', end_date, allow_null)) }}
{%- endmacro %}

{% macro rule_required_when(required_expression, when_expression) -%}
  (not coalesce(({{ when_expression }}), false) or {{ required_expression }} is not null)
{%- endmacro %}

{% macro rule_sum_equals(total, components, tolerance=0, allow_null=false) -%}
  {% if components | length == 0 %}{{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.rule_sum_equals components cannot be empty.') }}{% endif %}
  (case
    when {{ total }} is null
      {%- for component in components %} or {{ component }} is null{% endfor %}
      then {{ 'true' if allow_null else 'false' }}
    else abs({{ total }} - (
    {%- for component in components -%}
      ({{ component }}){{ ' + ' if not loop.last }}
    {%- endfor -%}
    )) <= {{ tolerance }}
  end)
{%- endmacro %}

{% macro rule_one_of(expressions) -%}
  {% if expressions | length == 0 %}{{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.rule_one_of expressions cannot be empty.') }}{% endif %}
  (({%- for expression in expressions -%}case when {{ expression }} is not null then 1 else 0 end{{ ' + ' if not loop.last }}{%- endfor -%}) = 1)
{%- endmacro %}
