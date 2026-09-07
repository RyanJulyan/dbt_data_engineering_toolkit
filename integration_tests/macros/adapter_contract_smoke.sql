{% macro adapter_contract_smoke() %}
  {# Render adapter-dispatched SQL without opening a warehouse connection. #}
  {% set expressions = [
      dbt_data_engineering_toolkit.clean_string("'  Ada   Lovelace  '"),
      dbt_data_engineering_toolkit.clean_numeric("'1234.5'", 18, 2),
      dbt_data_engineering_toolkit.clean_date("'2026-09-04'"),
      dbt_data_engineering_toolkit.format_date("cast('2026-09-04' as date)", '%d/%m/%Y'),
      dbt_data_engineering_toolkit.format_number("'1234.5'", 2, true),
      dbt_data_engineering_toolkit.is_email("'ada@example.com'"),
      dbt_data_engineering_toolkit.clean_phone("'+1 (202) 555-0100'"),
      dbt_data_engineering_toolkit.string_split_part("'a,b'", ',', 2),
      dbt_data_engineering_toolkit.percentile('amount', 0.5),
      dbt_data_engineering_toolkit.multi_hot("'a,b'", ['a', 'b'])
  ] %}
  {% for expression in expressions %}
    {% do log('DET adapter contract: ' ~ expression, info=true) %}
  {% endfor %}
  {{ return('') }}
{% endmacro %}
