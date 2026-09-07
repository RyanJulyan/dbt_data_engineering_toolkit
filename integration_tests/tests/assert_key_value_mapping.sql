select *
from {{ ref('stg_key_value_mapping') }}
where
  amount_display <> amount_display_operation
  or converted_date_operation <> '31 Dec 2026'
  or (id = 1 and (
    status_label <> 'ACTIVE'
    or amount_value <> 1234.50
    or amount_display <> 'R 1,234.50'
    or event_date <> cast('2026-09-04' as date)
    or event_date_display <> '04/09/2026'
    or enabled is not true
    or status_rank <> 10
    or event_at <> cast('2026-09-04 12:30:00' as {{ dbt.type_timestamp() }})
    or event_at_display <> '04/09/2026 12:30'
    or status_title <> 'Active'
    or explicit_null_default <> 'Active'
    or status_preserved <> 'Active'
  ))
  or (id = 2 and (
    status_label <> 'INACTIVE'
    or amount_value <> 98765.43
    or amount_display <> 'R 98,765.43'
    or event_date <> cast('2027-01-15' as date)
    or event_date_display <> '15/01/2027'
    or enabled is not false
    or status_rank <> 20
    or event_at <> cast('2027-01-15 08:00:00' as {{ dbt.type_timestamp() }})
    or event_at_display <> '15/01/2027 08:00'
    or status_title <> 'Inactive'
    or explicit_null_default is not null
    or status_preserved <> 'I'
  ))
  or (id = 3 and (
    status_label <> 'UNKNOWN'
    or amount_value is not null
    or amount_display <> 'INVALID'
    or event_date is not null
    or event_date_display <> 'INVALID DATE'
    or enabled is not false
    or status_rank <> 0
    or event_at is not null
    or event_at_display <> 'INVALID TIMESTAMP'
    or status_title <> 'Unknown'
    or explicit_null_default is not null
    or status_preserved <> 'X'
  ))
  or (id = 4 and (
    status_label <> 'UNKNOWN'
    or amount_value <> 0
    or amount_display <> 'R 0.00'
    or event_date <> cast('2026-01-01' as date)
    or event_date_display <> '01/01/2026'
    or enabled is not false
    or status_rank <> 0
    or event_at <> cast('2026-01-01 00:00:00' as {{ dbt.type_timestamp() }})
    or event_at_display <> '01/01/2026 00:00'
    or status_title <> 'Unknown'
    or explicit_null_default is not null
    or status_preserved is not null
  ))
  or (id = 5 and (
    status_label <> 'ACTIVE'
    or enabled is not true
    or status_rank <> 10
    or event_at <> cast('2026-09-04 12:30:00' as {{ dbt.type_timestamp() }})
    or event_at_display <> '04/09/2026 12:30'
    or status_title <> 'Active'
  ))
