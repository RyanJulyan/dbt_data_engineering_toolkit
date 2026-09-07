select *
from {{ ref('stg_customers') }}
where
    (customer_id = '1' and (
        customer_name <> 'Alice Smith'
        or email <> 'alice@example.com'
        or phone <> '+27825550101'
        or active is not true
        or revenue <> 100.25
        or country_code <> 'ZA'
    ))
    or (customer_id = '2' and (
        active is not false
        or revenue is not null
        or signup_date is not null
    ))
    or (customer_id = '3' and (
        customer_name is not null
        or phone is not null
        or active is not null
        or country_code <> 'US'
    ))

