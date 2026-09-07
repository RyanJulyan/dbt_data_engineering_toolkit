{% macro surrogate_key(fields) -%}{{ return(dbt_utils.generate_surrogate_key(fields)) }}{%- endmacro %}
{% macro safe_divide(numerator, denominator) -%}{{ return(dbt_utils.safe_divide(numerator, denominator)) }}{%- endmacro %}
{% macro safe_add(fields) -%}{{ return(dbt_utils.safe_add(fields)) }}{%- endmacro %}
{% macro safe_subtract(fields) -%}{{ return(dbt_utils.safe_subtract(fields)) }}{%- endmacro %}
{% macro deduplicate(relation, partition_by, order_by) -%}{{ return(dbt_utils.deduplicate(relation=relation, partition_by=partition_by, order_by=order_by)) }}{%- endmacro %}
{% macro union_relations(relations, column_override=none, include=none, exclude=none, source_column_name='_dbt_source_relation', where=none) -%}
  {{ return(dbt_utils.union_relations(relations=relations, column_override=column_override, include=include, exclude=exclude, source_column_name=source_column_name, where=where)) }}
{%- endmacro %}
{% macro date_spine(datepart, start_date, end_date) -%}{{ return(dbt_utils.date_spine(datepart=datepart, start_date=start_date, end_date=end_date)) }}{%- endmacro %}

{# Private dependency adapters used by toolkit implementations. #}
{% macro _det_star(from, relation_alias=none) -%}
  {{ return(dbt_utils.star(from=from, relation_alias=relation_alias)) }}
{%- endmacro %}

{% macro _det_slugify(value) -%}
  {{ return(dbt_utils.slugify(value)) }}
{%- endmacro %}
