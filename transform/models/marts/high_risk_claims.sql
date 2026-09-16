select
    claim_id,
    policy_id,
    loss_date,
    reported_at,
    line_of_business,
    state,
    status,
    severity,
    reporting_delay_days,
    reserve_amount,
    paid_amount,
    total_incurred,
    risk_score,
    adjuster_id,
    source_system
from {{ ref('fct_claims_current') }}
where risk_score >= 70
order by risk_score desc, total_incurred desc

