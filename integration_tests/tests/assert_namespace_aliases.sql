select *
from {{ ref('stg_namespace_aliases') }}
where not _namespaces_match
   or not ({{ de_toolkit.keep_valid_rows() }})
