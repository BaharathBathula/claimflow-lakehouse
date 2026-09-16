select claim_id
from {{ ref('fct_claims_current') }}
where risk_score < 0 or risk_score > 100

