select * exclude (valid_to, is_current)
from {{ ref('dim_policy_history') }}
where is_current

