select
    loss_date,
    line_of_business,
    state,
    count(*) as claim_count,
    count(*) filter (where status not in ('closed', 'denied')) as open_claim_count,
    round(sum(paid_amount), 2) as paid_amount,
    round(sum(outstanding_reserve), 2) as outstanding_reserve,
    round(sum(total_incurred), 2) as total_incurred,
    round(avg(risk_score), 2) as avg_risk_score
from {{ ref('fct_claims_current') }}
group by 1, 2, 3

