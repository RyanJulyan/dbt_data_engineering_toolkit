{% macro _det_normalize_data_type(data_type) -%}
  {% if data_type is mapping %}
    {% set specification = data_type.copy() %}
    {% set requested = dbt_data_engineering_toolkit._det_required(specification, 'name', 'data_type') | lower %}
  {% else %}
    {% set specification = {'name': data_type} %}
    {% set requested = data_type | lower %}
  {% endif %}

  {% set aliases = {
      'str': 'string',
      'text': 'string',
      'int': 'integer',
      'number': 'numeric',
      'decimal': 'numeric',
      'datetime': 'timestamp',
      'bool': 'boolean'
  } %}
  {% set canonical = aliases.get(requested, requested) %}
  {% do dbt_data_engineering_toolkit._det_validate_choice(
      'data type', canonical,
      ['string', 'integer', 'numeric', 'date', 'timestamp', 'boolean']
  ) %}
  {% do specification.update({'name': canonical}) %}
  {{ return(specification) }}
{%- endmacro %}

{% macro convert_value(expression, data_type) -%}
  {% if data_type is none %}{{ return(expression) }}{% endif %}
  {% set specification = dbt_data_engineering_toolkit._det_normalize_data_type(data_type) %}
  {% set name = specification['name'] %}
  {% if name == 'string' %}
    {% set result %}cast({{ expression }} as {{ dbt.type_string() }}){% endset %}
  {% elif name == 'integer' %}
    {% set result = dbt_data_engineering_toolkit.clean_integer(expression) %}
  {% elif name == 'numeric' %}
    {% set result = dbt_data_engineering_toolkit.clean_numeric(
        expression,
        specification.get('precision', 38),
        specification.get('scale', 6)
    ) %}
  {% elif name == 'date' %}
    {% set result = dbt_data_engineering_toolkit.clean_date(expression) %}
  {% elif name == 'timestamp' %}
    {% set result = dbt_data_engineering_toolkit.clean_timestamp(expression) %}
  {% else %}
    {% set result = dbt_data_engineering_toolkit.clean_boolean(
        expression,
        specification.get('true_values', ['true', 't', 'yes', 'y', '1']),
        specification.get('false_values', ['false', 'f', 'no', 'n', '0'])
    ) %}
  {% endif %}
  {{ return(result) }}
{%- endmacro %}

{% macro _det_translate_pattern(pattern, dialect) -%}
  {% if dialect == 'to_char' %}
    {% set replacements = {
        '%Y': 'YYYY', '%y': 'YY', '%m': 'MM', '%d': 'DD',
        '%H': 'HH24', '%M': 'MI', '%S': 'SS',
        '%b': 'MON', '%B': 'MONTH', '%a': 'DY', '%A': 'DAY', '%j': 'DDD'
    } %}
  {% elif dialect == 'spark' %}
    {% set replacements = {
        '%Y': 'yyyy', '%y': 'yy', '%m': 'MM', '%d': 'dd',
        '%H': 'HH', '%M': 'mm', '%S': 'ss',
        '%b': 'MMM', '%B': 'MMMM', '%a': 'EEE', '%A': 'EEEE', '%j': 'DDD'
    } %}
  {% else %}
    {{ exceptions.raise_compiler_error("dbt_data_engineering_toolkit: unknown date-format dialect '" ~ dialect ~ "'.") }}
  {% endif %}
  {% set state = namespace(result=pattern) %}
  {% for source, target in replacements.items() %}
    {% set state.result = state.result | replace(source, target) %}
  {% endfor %}
  {{ return(state.result) }}
{%- endmacro %}

{% macro format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  {% set specification = dbt_data_engineering_toolkit._det_normalize_data_type(data_type) %}
  {% if specification['name'] not in ['date', 'timestamp'] %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.format_temporal requires date or timestamp data_type.') }}
  {% endif %}
  {{ return(adapter.dispatch('format_temporal', 'dbt_data_engineering_toolkit')(
      expression, specification['name'], pattern
  )) }}
{%- endmacro %}

{% macro default__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  {{ exceptions.raise_compiler_error(
      "dbt_data_engineering_toolkit.format_temporal is not implemented for adapter '" ~ target.type ~ "'."
  ) }}
{%- endmacro %}

{% macro duckdb__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  strftime({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(pattern) }})
{%- endmacro %}

{% macro bigquery__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  {% if data_type == 'date' %}
    format_date({{ dbt_data_engineering_toolkit._det_sql_string(pattern) }}, {{ expression }})
  {% else %}
    format_timestamp({{ dbt_data_engineering_toolkit._det_sql_string(pattern) }}, {{ expression }})
  {% endif %}
{%- endmacro %}

{% macro postgres__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  to_char({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_translate_pattern(pattern, 'to_char')) }})
{%- endmacro %}

{% macro redshift__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  to_char({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_translate_pattern(pattern, 'to_char')) }})
{%- endmacro %}

{% macro snowflake__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  to_varchar({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_translate_pattern(pattern, 'to_char')) }})
{%- endmacro %}

{% macro databricks__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  date_format({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_translate_pattern(pattern, 'spark')) }})
{%- endmacro %}

{% macro spark__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  date_format({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_translate_pattern(pattern, 'spark')) }})
{%- endmacro %}

{% macro athena__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  date_format({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(pattern) }})
{%- endmacro %}

{% macro clickhouse__format_temporal(expression, data_type, pattern='%Y-%m-%d') -%}
  formatDateTime({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(pattern) }})
{%- endmacro %}

{% macro _det_grouped_number(expression, decimal_places) -%}
  {{ return(adapter.dispatch('_det_grouped_number', 'dbt_data_engineering_toolkit')(expression, decimal_places)) }}
{%- endmacro %}

{% macro default___det_grouped_number(expression, decimal_places) -%}
  {{ exceptions.raise_compiler_error(
      "dbt_data_engineering_toolkit grouped number formatting is not implemented for adapter '" ~ target.type ~ "'. Set grouping=false or add dispatch."
  ) }}
{%- endmacro %}

{% macro duckdb___det_grouped_number(expression, decimal_places) -%}
  printf({{ dbt_data_engineering_toolkit._det_sql_string('%,.' ~ decimal_places ~ 'f') }}, {{ expression }})
{%- endmacro %}

{% macro bigquery___det_grouped_number(expression, decimal_places) -%}
  format({{ dbt_data_engineering_toolkit._det_sql_string("%'" ~ '.' ~ decimal_places ~ 'f') }}, {{ expression }})
{%- endmacro %}

{% macro databricks___det_grouped_number(expression, decimal_places) -%}
  format_number({{ expression }}, {{ decimal_places }})
{%- endmacro %}

{% macro spark___det_grouped_number(expression, decimal_places) -%}
  format_number({{ expression }}, {{ decimal_places }})
{%- endmacro %}

{% macro athena___det_grouped_number(expression, decimal_places) -%}
  format({{ dbt_data_engineering_toolkit._det_sql_string('%,' ~ '.' ~ decimal_places ~ 'f') }}, cast({{ expression }} as double))
{%- endmacro %}

{% macro clickhouse___det_grouped_number(expression, decimal_places) -%}
  {% set fixed %}replaceOne(toString(ifNull({{ expression }}, 0)), '-', ''){% endset %}
  {% set integer_part %}arrayElement(splitByChar('.', {{ fixed }}), 1){% endset %}
  if(
    isNull({{ expression }}),
    cast(null as Nullable(String)),
    concat(
      if({{ expression }} < 0, '-', ''),
      arrayStringConcat(
        arrayMap(
          chunk -> reverse(chunk),
          arrayReverse(
            arrayMap(
              offset -> substring(reverse({{ integer_part }}), offset * 3 + 1, 3),
              range(toUInt64(intDiv(length({{ integer_part }}) + 2, 3)))
            )
          )
        ),
        ','
      )
      {% if decimal_places > 0 %}
        , '.', arrayElement(splitByChar('.', {{ fixed }}), 2)
      {% endif %}
    )
  )
{%- endmacro %}

{% macro _det_to_char_number_pattern(decimal_places) -%}
  {% set groups = [] %}
  {% for _ in range(12) %}{% do groups.append('999') %}{% endfor %}
  {% do groups.append('990') %}
  {% set pattern = 'FM' ~ groups | join('G') %}
  {% if decimal_places > 0 %}
    {% set pattern = pattern ~ 'D' ~ ('0' * decimal_places) %}
  {% endif %}
  {{ return(pattern) }}
{%- endmacro %}

{% macro postgres___det_grouped_number(expression, decimal_places) -%}
  to_char({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_to_char_number_pattern(decimal_places)) }})
{%- endmacro %}

{% macro redshift___det_grouped_number(expression, decimal_places) -%}
  to_char({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_to_char_number_pattern(decimal_places)) }})
{%- endmacro %}

{% macro snowflake___det_grouped_number(expression, decimal_places) -%}
  to_varchar({{ expression }}, {{ dbt_data_engineering_toolkit._det_sql_string(dbt_data_engineering_toolkit._det_to_char_number_pattern(decimal_places)) }})
{%- endmacro %}

{% macro format_number(expression, decimal_places=none, grouping=false, prefix='', suffix='', null_value=none) -%}
  {% if decimal_places is none %}{% set decimal_places = 0 %}{% endif %}
  {% if decimal_places < 0 or decimal_places > 38 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.format_number requires 0 <= decimal_places <= 38.') }}
  {% endif %}
  {% set numeric_value = dbt_data_engineering_toolkit.clean_numeric(expression, 38, decimal_places) %}
  {% if grouping %}
    {% set formatted = dbt_data_engineering_toolkit._det_grouped_number(numeric_value, decimal_places) %}
  {% else %}
    {% set formatted %}cast({{ numeric_value }} as {{ dbt.type_string() }}){% endset %}
  {% endif %}
  {% if prefix != '' or suffix != '' %}
    {% set formatted %}case
      when {{ formatted }} is null then null
      else concat(
        {{ dbt_data_engineering_toolkit._det_sql_string(prefix) }},
        {{ formatted }},
        {{ dbt_data_engineering_toolkit._det_sql_string(suffix) }}
      )
    end{% endset %}
  {% endif %}
  {% if null_value is not none %}
    {% set formatted %}coalesce({{ formatted }}, {{ dbt_data_engineering_toolkit._det_sql_string(null_value) }}){% endset %}
  {% endif %}
  {{ return(formatted) }}
{%- endmacro %}

{% macro format_value(expression, data_type, formatting=none) -%}
  {% if formatting is none %}{{ return(expression) }}{% endif %}
  {% set specification = dbt_data_engineering_toolkit._det_normalize_data_type(data_type) %}
  {% set name = specification['name'] %}

  {% if formatting is string %}
    {% if name in ['date', 'timestamp'] %}
      {% set formatting = {'pattern': formatting} %}
    {% elif name == 'string' %}
      {% set formatting = {'case': formatting} %}
    {% else %}
      {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.format_value: numeric formatting must be a mapping.') }}
    {% endif %}
  {% endif %}
  {% do dbt_data_engineering_toolkit._det_assert_mapping(formatting, 'formatting') %}

  {% if name in ['date', 'timestamp'] %}
    {% set result = dbt_data_engineering_toolkit.format_temporal(
        expression, specification, formatting.get('pattern', '%Y-%m-%d')
    ) %}
  {% elif name in ['numeric', 'integer'] %}
    {% set default_places = specification.get('scale', 6) if name == 'numeric' else 0 %}
    {% set result = dbt_data_engineering_toolkit.format_number(
        expression,
        formatting.get('decimal_places', default_places),
        formatting.get('grouping', false),
        formatting.get('prefix', ''),
        formatting.get('suffix', ''),
        formatting.get('null_value')
    ) %}
  {% elif name == 'string' %}
    {% set requested_case = formatting.get('case', 'preserve') %}
    {% do dbt_data_engineering_toolkit._det_validate_choice(
        'string format case', requested_case,
        ['preserve', 'lower', 'upper', 'title', 'capitalize']
    ) %}
    {% set base_case = requested_case if requested_case in ['lower', 'upper'] else 'preserve' %}
    {% set result = dbt_data_engineering_toolkit.clean_string(
        expression,
        formatting.get('trim', false),
        formatting.get('collapse_whitespace', false),
        base_case,
        formatting.get('blank_as_null', false)
    ) %}
    {% if requested_case == 'title' %}
      {% set result = dbt_data_engineering_toolkit.string_title(result) %}
    {% elif requested_case == 'capitalize' %}
      {% set result = dbt_data_engineering_toolkit.string_capitalize(result) %}
    {% endif %}
  {% else %}
    {% set result %}cast({{ expression }} as {{ dbt.type_string() }}){% endset %}
  {% endif %}

  {% if 'null_value' in formatting and name not in ['numeric', 'integer'] %}
    {% set result %}coalesce({{ result }}, {{ dbt_data_engineering_toolkit._det_sql_string(formatting['null_value']) }}){% endset %}
  {% endif %}
  {{ return(result) }}
{%- endmacro %}
