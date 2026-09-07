select *
from {{ ref('stg_cleaning_operations') }}
where
  (id = 1 and (
    cleaned_text <> 'hello world'
    or corrected_code <> 'OK'
    or category_label <> 0
    or amount_filled <> -5
    or amount_clipped <> 0
    or abs(amount_scaled - 0) > 0.000001
    or category_alpha <> 1
    or category_beta <> 0
    or tag_red <> 1
    or tag_blue <> 1
    or tag_gold <> 0
    or second_tag <> 'blue'
    or padded_number <> '-0007'
    or code_slice <> 'ER'
    or code_replaced <> 'XRR'
    or amount_band <> 'low'
  ))
  or (id = 2 and (
    cleaned_text <> 'dataops'
    or corrected_code <> 'OK'
    or category_label <> 1
    or amount_clipped <> 25
    or tag_red <> 0
    or tag_blue <> 0
    or tag_gold <> 1
    or second_tag <> 'gold'
    or padded_number <> '00042'
    or amount_band <> 'medium'
  ))
  or (id = 3 and (
    cleaned_text <> 'mixedcase'
    or corrected_code <> 'CURRENT'
    or amount_clipped <> 100
    or abs(amount_scaled - 1) > 0.000001
    or amount_band <> 'high'
  ))
  or (id = 4 and (
    category_label <> -1
    or amount_filled <> 0
    or amount_clipped is not null
    or amount_band is not null
  ))
