{% test expression_true(model, expression) %}
select * from {{ model }} where not coalesce(({{ expression }}), false)
{% endtest %}

{% test valid_email(model, column_name, allow_null=false) %}
select * from {{ model }} where not {{ dbt_data_engineering_toolkit.is_email(column_name, allow_null) }}
{% endtest %}

{% test no_future_dates(model, column_name, allow_null=true) %}
select * from {{ model }}
where not (case when {{ column_name }} is null then {{ 'true' if allow_null else 'false' }} else {{ column_name }} <= {{ dbt.current_timestamp() }} end)
{% endtest %}

{% test minimum_variance(model, column_name, threshold=0) %}
with validation as (
  select var_samp({{ column_name }}) as variance_value
  from {{ model }}
)
select *
from validation
where variance_value is null or variance_value <= {{ threshold }}
{% endtest %}

{% test correlation_below(model, column_name, compare_column, maximum=0.8) %}
with validation as (
  select corr({{ column_name }}, {{ compare_column }}) as correlation_value
  from {{ model }}
)
select *
from validation
where abs(correlation_value) > {{ maximum }}
{% endtest %}

{% test correlation_above(model, column_name, target_column, minimum=0.2) %}
with validation as (
  select corr({{ column_name }}, {{ target_column }}) as correlation_value
  from {{ model }}
)
select *
from validation
where correlation_value is null or abs(correlation_value) < {{ minimum }}
{% endtest %}
