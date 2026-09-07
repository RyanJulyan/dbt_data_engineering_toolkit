{% macro _det_window_clause(partition_by=none) -%}
  {% if partition_by is none or partition_by == '' %}
    {{ return('over ()') }}
  {% endif %}
  {{ return('over (partition by ' ~ partition_by ~ ')') }}
{%- endmacro %}

{% macro min_max_scale(expression, partition_by=none, zero_range_value=0) -%}
  {% set window = dbt_data_engineering_toolkit._det_window_clause(partition_by) %}
  {% set minimum %}min({{ expression }}) {{ window }}{% endset %}
  {% set maximum %}max({{ expression }}) {{ window }}{% endset %}
  case
    when {{ expression }} is null then null
    when {{ maximum }} = {{ minimum }} then {{ dbt_data_engineering_toolkit._det_sql_literal(zero_range_value) }}
    else cast({{ expression }} - {{ minimum }} as {{ dbt.type_float() }}) / nullif({{ maximum }} - {{ minimum }}, 0)
  end
{%- endmacro %}

{% macro standard_score(expression, partition_by=none, zero_variance_value=none) -%}
  {% set window = dbt_data_engineering_toolkit._det_window_clause(partition_by) %}
  {% set average %}avg({{ expression }}) {{ window }}{% endset %}
  {% set deviation %}stddev_samp({{ expression }}) {{ window }}{% endset %}
  case
    when {{ expression }} is null then null
    when {{ deviation }} is null or {{ deviation }} = 0 then {{ dbt_data_engineering_toolkit._det_sql_literal(zero_variance_value) }}
    else cast({{ expression }} - {{ average }} as {{ dbt.type_float() }}) / nullif({{ deviation }}, 0)
  end
{%- endmacro %}

{% macro clip(expression, lower, upper) -%}
  {% if lower is number and upper is number and lower > upper %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.clip: lower must be <= upper.') }}
  {% endif %}
  case
    when {{ expression }} is null then null
    when {{ expression }} < {{ lower }} then {{ lower }}
    when {{ expression }} > {{ upper }} then {{ upper }}
    else {{ expression }}
  end
{%- endmacro %}

{% macro winsorize(expression, lower_bound, upper_bound) -%}
  {{ return(dbt_data_engineering_toolkit.clip(expression, lower_bound, upper_bound)) }}
{%- endmacro %}

{% macro within_bounds(expression, lower, upper, allow_null=false) -%}
  case
    when {{ expression }} is null then {{ 'true' if allow_null else 'false' }}
    else {{ expression }} between {{ lower }} and {{ upper }}
  end
{%- endmacro %}

{% macro replace_outside_bounds(expression, lower, upper, replacement) -%}
  case
    when {{ expression }} between {{ lower }} and {{ upper }} then {{ expression }}
    when {{ expression }} is null then null
    else {{ replacement }}
  end
{%- endmacro %}

{% macro log_transform(expression, offset=1) -%}
  ln({{ expression }} + {{ offset }})
{%- endmacro %}

{% macro bin_numeric(expression, edges, labels=none, right=true, include_lowest=false) -%}
  {% do dbt_data_engineering_toolkit._det_assert_sequence(edges, 'edges') %}
  {% if edges | length < 2 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.bin_numeric: edges must contain at least two values.') }}
  {% endif %}
  {% if labels is not none %}
    {% do dbt_data_engineering_toolkit._det_assert_sequence(labels, 'labels') %}
    {% if labels | length != (edges | length - 1) %}
      {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.bin_numeric: labels must have exactly len(edges) - 1 values.') }}
    {% endif %}
  {% endif %}
  case
    {% for lower in edges[:-1] %}
      {% set upper = edges[loop.index] %}
      {% set result = labels[loop.index0] if labels is not none else loop.index0 %}
      when
        {% if right %}
          {{ expression }} {{ '>=' if include_lowest and loop.first else '>' }} {{ lower }} and {{ expression }} <= {{ upper }}
        {% else %}
          {{ expression }} >= {{ lower }} and {{ expression }} < {{ upper }}
        {% endif %}
        then {{ dbt_data_engineering_toolkit._det_sql_literal(result) }}
    {% endfor %}
    else null
  end
{%- endmacro %}

{% macro percentile(expression, percentile, partition_by=none) -%}
  {% if percentile < 0 or percentile > 1 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.percentile: percentile must be between 0 and 1.') }}
  {% endif %}
  {{ return(adapter.dispatch('percentile', 'dbt_data_engineering_toolkit')(expression, percentile, partition_by)) }}
{%- endmacro %}

{% macro default__percentile(expression, percentile, partition_by=none) -%}
  {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.percentile is not supported for adapter ' ~ target.type ~ '. Add an adapter dispatch implementation.') }}
{%- endmacro %}

{% macro duckdb__percentile(expression, percentile, partition_by=none) -%}
  quantile_cont({{ expression }}, {{ percentile }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro bigquery__percentile(expression, percentile, partition_by=none) -%}
  percentile_cont({{ expression }}, {{ percentile }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro snowflake__percentile(expression, percentile, partition_by=none) -%}
  percentile_cont({{ percentile }}) within group (order by {{ expression }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro databricks__percentile(expression, percentile, partition_by=none) -%}
  percentile({{ expression }}, {{ percentile }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro spark__percentile(expression, percentile, partition_by=none) -%}
  percentile({{ expression }}, {{ percentile }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro redshift__percentile(expression, percentile, partition_by=none) -%}
  percentile_cont({{ percentile }}) within group (order by {{ expression }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro athena__percentile(expression, percentile, partition_by=none) -%}
  approx_percentile({{ expression }}, {{ percentile }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro clickhouse__percentile(expression, percentile, partition_by=none) -%}
  quantileExact({{ percentile }})({{ expression }}) {{ dbt_data_engineering_toolkit._det_window_clause(partition_by) }}
{%- endmacro %}

{% macro is_iqr_anomaly(expression, q1_expression, q3_expression, threshold=1.5) -%}
  case
    when {{ expression }} is null or {{ q1_expression }} is null or {{ q3_expression }} is null then false
    else {{ expression }} < ({{ q1_expression }} - {{ threshold }} * ({{ q3_expression }} - {{ q1_expression }}))
      or {{ expression }} > ({{ q3_expression }} + {{ threshold }} * ({{ q3_expression }} - {{ q1_expression }}))
  end
{%- endmacro %}

{% macro is_zscore_anomaly(expression, threshold=3, partition_by=none) -%}
  coalesce(abs({{ dbt_data_engineering_toolkit.standard_score(expression, partition_by) }}) > {{ threshold }}, false)
{%- endmacro %}

{% macro is_modified_zscore_anomaly(expression, median_expression, mad_expression, threshold=3.5) -%}
  case
    when {{ expression }} is null or {{ mad_expression }} is null or {{ mad_expression }} = 0 then false
    else abs(0.6745 * ({{ expression }} - {{ median_expression }}) / {{ mad_expression }}) > {{ threshold }}
  end
{%- endmacro %}
