select
    count(*) as total_claims,
    count(*) filter (where status not in ('closed', 'denied')) as open_claims,
    round(sum(total_incurred), 2) as total_incurred,
    round(sum(paid_amount), 2) as total_paid,
    round(sum(outstanding_reserve), 2) as outstanding_reserve,
    count(*) filter (where risk_score >= 70) as high_risk_claims,
    round(avg(reporting_delay_days), 2) as avg_reporting_delay_days,
    max(occurred_at) as data_as_of
from {{ ref('fct_claims_current') }}

