select claim_id
from {{ ref('fct_claims_current') }}
where reserve_amount < 0
   or paid_amount < 0
   or outstanding_reserve < 0
   or total_incurred < 0

