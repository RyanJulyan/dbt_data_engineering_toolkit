{% macro string_lower(expression) -%}
  lower(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro string_upper(expression) -%}
  upper(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro string_title(expression) -%}
  {{ return(adapter.dispatch('string_title', 'dbt_data_engineering_toolkit')(expression)) }}
{%- endmacro %}

{% macro default__string_title(expression) -%}
  initcap(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro duckdb__string_title(expression) -%}
  array_to_string(
    list_transform(
      string_split(lower(cast({{ expression }} as {{ dbt.type_string() }})), ' '),
      lambda word: concat(upper(substr(word, 1, 1)), substr(word, 2))
    ),
    ' '
  )
{%- endmacro %}

{% macro athena__string_title(expression) -%}
  array_join(
    transform(
      split(lower(cast({{ expression }} as {{ dbt.type_string() }})), ' '),
      word -> concat(upper(substr(word, 1, 1)), substr(word, 2))
    ),
    ' '
  )
{%- endmacro %}

{% macro clickhouse__string_title(expression) -%}
  initcapUTF8(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro string_capitalize(expression) -%}
  concat(
    upper(substr(cast({{ expression }} as {{ dbt.type_string() }}), 1, 1)),
    lower(substr(cast({{ expression }} as {{ dbt.type_string() }}), 2))
  )
{%- endmacro %}

{% macro string_casefold(expression) -%}
  {# SQL lower() is the portable cross-adapter approximation. #}
  {{ return(dbt_data_engineering_toolkit.string_lower(expression)) }}
{%- endmacro %}

{% macro string_strip(expression) -%}
  trim(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro string_left_strip(expression) -%}
  ltrim(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro string_right_strip(expression) -%}
  rtrim(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro string_split_part(expression, delimiter=',', part=1) -%}
  {% if part < 1 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_split_part: part must be >= 1.') }}
  {% endif %}
  {{ return(adapter.dispatch('string_split_part', 'dbt_data_engineering_toolkit')(expression, delimiter, part)) }}
{%- endmacro %}

{% macro default__string_split_part(expression, delimiter=',', part=1) -%}
  split_part(
    cast({{ expression }} as {{ dbt.type_string() }}),
    {{ dbt_data_engineering_toolkit._det_sql_string(delimiter) }},
    {{ part }}
  )
{%- endmacro %}

{% macro bigquery__string_split_part(expression, delimiter=',', part=1) -%}
  split(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_sql_string(delimiter) }})[safe_offset({{ part - 1 }})]
{%- endmacro %}

{% macro clickhouse__string_split_part(expression, delimiter=',', part=1) -%}
  arrayElement(
    splitByString({{ dbt_data_engineering_toolkit._det_sql_string(delimiter) }}, cast({{ expression }} as {{ dbt.type_string() }})),
    {{ part }}
  )
{%- endmacro %}

{% macro string_remove_prefix(expression, prefix) -%}
  {% if prefix == '' %}{{ return(expression) }}{% endif %}
  {% set prefix_sql = dbt_data_engineering_toolkit._det_sql_string(prefix) %}
  case
    when substr(cast({{ expression }} as {{ dbt.type_string() }}), 1, length({{ prefix_sql }})) = {{ prefix_sql }}
      then substr(cast({{ expression }} as {{ dbt.type_string() }}), length({{ prefix_sql }}) + 1)
    else cast({{ expression }} as {{ dbt.type_string() }})
  end
{%- endmacro %}

{% macro string_remove_suffix(expression, suffix) -%}
  {% if suffix == '' %}{{ return(expression) }}{% endif %}
  {% set suffix_sql = dbt_data_engineering_toolkit._det_sql_string(suffix) %}
  case
    when substr(cast({{ expression }} as {{ dbt.type_string() }}), -length({{ suffix_sql }})) = {{ suffix_sql }}
      then substr(cast({{ expression }} as {{ dbt.type_string() }}), 1, length(cast({{ expression }} as {{ dbt.type_string() }})) - length({{ suffix_sql }}))
    else cast({{ expression }} as {{ dbt.type_string() }})
  end
{%- endmacro %}

{% macro string_pad(expression, width, side='both', fillchar=' ') -%}
  {% do dbt_data_engineering_toolkit._det_validate_choice('pad side', side, ['both', 'left', 'right']) %}
  {% if width < 0 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_pad: width must be >= 0.') }}
  {% endif %}
  {% if fillchar | length != 1 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_pad: fillchar must be exactly one character.') }}
  {% endif %}
  {% set value %}cast({{ expression }} as {{ dbt.type_string() }}){% endset %}
  {% set fill = dbt_data_engineering_toolkit._det_sql_string(fillchar) %}
  {% if side == 'left' %}
    lpad({{ value }}, {{ width }}, {{ fill }})
  {% elif side == 'right' %}
    rpad({{ value }}, {{ width }}, {{ fill }})
  {% else %}
    rpad(
      lpad(
        {{ value }},
        cast(length({{ value }}) + floor(greatest({{ width }} - length({{ value }}), 0) / 2) as {{ dbt.type_int() }}),
        {{ fill }}
      ),
      {{ width }},
      {{ fill }}
    )
  {% endif %}
{%- endmacro %}

{% macro string_center(expression, width, fillchar=' ') -%}
  {{ return(dbt_data_engineering_toolkit.string_pad(expression, width, 'both', fillchar)) }}
{%- endmacro %}

{% macro string_ljust(expression, width, fillchar=' ') -%}
  {{ return(dbt_data_engineering_toolkit.string_pad(expression, width, 'right', fillchar)) }}
{%- endmacro %}

{% macro string_rjust(expression, width, fillchar=' ') -%}
  {{ return(dbt_data_engineering_toolkit.string_pad(expression, width, 'left', fillchar)) }}
{%- endmacro %}

{% macro string_zfill(expression, width) -%}
  {% if width < 0 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_zfill: width must be >= 0.') }}
  {% endif %}
  {% set value %}cast({{ expression }} as {{ dbt.type_string() }}){% endset %}
  case
    when substr({{ value }}, 1, 1) in ('+', '-')
      then concat(substr({{ value }}, 1, 1), lpad(substr({{ value }}, 2), greatest({{ width }} - 1, 0), '0'))
    else lpad({{ value }}, {{ width }}, '0')
  end
{%- endmacro %}

{% macro string_slice(expression, start=none, stop=none) -%}
  {% set start = 0 if start is none else start %}
  {% if start < 0 or (stop is not none and stop < 0) %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_slice: negative indexes are not portable; use a warehouse-specific expression.') }}
  {% endif %}
  {% if stop is not none and stop < start %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_slice: stop must be >= start.') }}
  {% endif %}
  {% if stop is none %}
    substr(cast({{ expression }} as {{ dbt.type_string() }}), {{ start + 1 }})
  {% else %}
    substr(cast({{ expression }} as {{ dbt.type_string() }}), {{ start + 1 }}, {{ stop - start }})
  {% endif %}
{%- endmacro %}

{% macro string_slice_replace(expression, start=none, stop=none, replacement='') -%}
  {% set start = 0 if start is none else start %}
  {% if start < 0 or (stop is not none and stop < 0) %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_slice_replace: negative indexes are not portable.') }}
  {% endif %}
  {% if stop is not none and stop < start %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_slice_replace: stop must be >= start.') }}
  {% endif %}
  {% set value %}cast({{ expression }} as {{ dbt.type_string() }}){% endset %}
  concat(
    substr({{ value }}, 1, {{ start }}),
    {{ dbt_data_engineering_toolkit._det_sql_string(replacement) }}
    {% if stop is not none %}, substr({{ value }}, {{ stop + 1 }}){% endif %}
  )
{%- endmacro %}

{% macro string_regex_extract(expression, pattern, group=1) -%}
  {{ return(adapter.dispatch('string_regex_extract', 'dbt_data_engineering_toolkit')(expression, pattern, group)) }}
{%- endmacro %}

{% macro default__string_regex_extract(expression, pattern, group=1) -%}
  regexp_extract(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ group }})
{%- endmacro %}

{% macro bigquery__string_regex_extract(expression, pattern, group=1) -%}
  {% if group != 1 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_regex_extract: BigQuery requires exactly one capturing group and group=1 through this portable facade.') }}
  {% endif %}
  regexp_extract(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }})
{%- endmacro %}

{% macro snowflake__string_regex_extract(expression, pattern, group=1) -%}
  {% if group == 0 %}
    regexp_substr(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }})
  {% else %}
    regexp_substr(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, 1, 1, 'e', {{ group }})
  {% endif %}
{%- endmacro %}

{% macro redshift__string_regex_extract(expression, pattern, group=1) -%}
  {% if group not in [0, 1] %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_regex_extract: Redshift supports group 0 or 1 through this portable facade.') }}
  {% endif %}
  regexp_substr(
    cast({{ expression }} as {{ dbt.type_string() }}),
    {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }},
    1,
    1{% if group == 1 %}, 'e'{% endif %}
  )
{%- endmacro %}

{% macro clickhouse__string_regex_extract(expression, pattern, group=1) -%}
  {% if group < 1 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_regex_extract: ClickHouse requires a capture group numbered 1 or greater.') }}
  {% endif %}
  arrayElement(
    extractGroups(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}),
    {{ group }}
  )
{%- endmacro %}

{% macro string_regex_extract_all(expression, pattern, group=1) -%}
  {{ return(adapter.dispatch('string_regex_extract_all', 'dbt_data_engineering_toolkit')(expression, pattern, group)) }}
{%- endmacro %}

{% macro default__string_regex_extract_all(expression, pattern, group=1) -%}
  {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_regex_extract_all is not supported for adapter ' ~ target.type ~ '. Add an adapter dispatch implementation.') }}
{%- endmacro %}

{% macro duckdb__string_regex_extract_all(expression, pattern, group=1) -%}
  regexp_extract_all(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ group }})
{%- endmacro %}

{% macro bigquery__string_regex_extract_all(expression, pattern, group=1) -%}
  {% if group != 1 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_regex_extract_all: BigQuery requires exactly one capturing group and group=1 through this portable facade.') }}
  {% endif %}
  regexp_extract_all(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }})
{%- endmacro %}

{% macro snowflake__string_regex_extract_all(expression, pattern, group=1) -%}
  {% if group == 0 %}
    regexp_substr_all(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }})
  {% else %}
    regexp_substr_all(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, 1, 'e', {{ group }})
  {% endif %}
{%- endmacro %}

{% macro databricks__string_regex_extract_all(expression, pattern, group=1) -%}
  regexp_extract_all(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ group }})
{%- endmacro %}

{% macro spark__string_regex_extract_all(expression, pattern, group=1) -%}
  regexp_extract_all(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ group }})
{%- endmacro %}

{% macro athena__string_regex_extract_all(expression, pattern, group=1) -%}
  regexp_extract_all(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }}, {{ group }})
{%- endmacro %}

{% macro clickhouse__string_regex_extract_all(expression, pattern, group=1) -%}
  {% if group != 1 %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.string_regex_extract_all: ClickHouse supports capture group 1 through this portable facade.') }}
  {% endif %}
  extractAll(cast({{ expression }} as {{ dbt.type_string() }}), {{ dbt_data_engineering_toolkit._det_regex_string(pattern) }})
{%- endmacro %}

{% macro string_remove_punctuation(expression) -%}
  {{ return(dbt_data_engineering_toolkit.regex_replace_all(expression, '[[:punct:]]', '')) }}
{%- endmacro %}

{% macro string_remove_whitespace(expression) -%}
  {{ return(dbt_data_engineering_toolkit.string_strip(expression)) }}
{%- endmacro %}

{% macro string_remove_all_whitespace(expression) -%}
  {{ return(dbt_data_engineering_toolkit.regex_replace_all(expression, '[[:space:]]+', '')) }}
{%- endmacro %}

{% macro string_replace_many(expression, replacements) -%}
  {% do dbt_data_engineering_toolkit._det_assert_mapping(replacements, 'replacements') %}
  {% set state = namespace(result='cast(' ~ expression ~ ' as ' ~ dbt.type_string() ~ ')') %}
  {% for old, new in replacements.items() %}
    {% set state.result %}replace({{ state.result }}, {{ dbt_data_engineering_toolkit._det_sql_string(old) }}, {{ dbt_data_engineering_toolkit._det_sql_string(new) }}){% endset %}
  {% endfor %}
  {{ return(state.result) }}
{%- endmacro %}

{% macro string_regex_replace_many(expression, replacements) -%}
  {% do dbt_data_engineering_toolkit._det_assert_mapping(replacements, 'replacements') %}
  {% set state = namespace(result='cast(' ~ expression ~ ' as ' ~ dbt.type_string() ~ ')') %}
  {% for pattern, replacement in replacements.items() %}
    {% set state.result = dbt_data_engineering_toolkit.regex_replace_all(state.result, pattern, replacement) %}
  {% endfor %}
  {{ return(state.result) }}
{%- endmacro %}

{% macro string_translate_chars(expression, translations) -%}
  {# Nested replacement is deterministic and works for character and substring maps. #}
  {{ return(dbt_data_engineering_toolkit.string_replace_many(expression, translations)) }}
{%- endmacro %}

{% macro unicode_normalize(expression, form='NFC') -%}
  {% do dbt_data_engineering_toolkit._det_validate_choice('Unicode normalization form', form, ['NFC', 'NFD', 'NFKC', 'NFKD']) %}
  {{ return(adapter.dispatch('unicode_normalize', 'dbt_data_engineering_toolkit')(expression, form)) }}
{%- endmacro %}

{% macro default__unicode_normalize(expression, form='NFC') -%}
  {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.unicode_normalize is not supported for adapter ' ~ target.type ~ '. Normalize upstream or add adapter dispatch.') }}
{%- endmacro %}

{% macro bigquery__unicode_normalize(expression, form='NFC') -%}
  normalize(cast({{ expression }} as {{ dbt.type_string() }}), {{ form }})
{%- endmacro %}

{% macro duckdb__unicode_normalize(expression, form='NFC') -%}
  {% if form != 'NFC' %}
    {{ exceptions.raise_compiler_error('dbt_data_engineering_toolkit.unicode_normalize: DuckDB supports NFC only.') }}
  {% endif %}
  nfc_normalize(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}

{% macro athena__unicode_normalize(expression, form='NFC') -%}
  normalize(cast({{ expression }} as {{ dbt.type_string() }}), {{ form }})
{%- endmacro %}

{% macro clickhouse__unicode_normalize(expression, form='NFC') -%}
  {% set functions = {
      'NFC': 'normalizeUTF8NFC',
      'NFD': 'normalizeUTF8NFD',
      'NFKC': 'normalizeUTF8NFKC',
      'NFKD': 'normalizeUTF8NFKD'
  } %}
  {{ functions[form] }}(cast({{ expression }} as {{ dbt.type_string() }}))
{%- endmacro %}
