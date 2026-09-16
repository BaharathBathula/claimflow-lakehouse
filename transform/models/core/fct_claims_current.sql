with latest_claim as (
    select * exclude (claim_rank)
    from (
        select
            *,
            row_number() over (
                partition by claim_id order by occurred_at desc, event_id desc
            ) as claim_rank
        from {{ ref('stg_claims') }}
    )
    where claim_rank = 1
),

payments as (
    select
        claim_id,
        sum(case when payment_status != 'void' then amount else 0 end) as cleared_payment_amount,
        count(case when payment_status != 'void' then 1 end) as payment_count
    from {{ ref('stg_payments') }}
    group by claim_id
),

enriched as (
    select
        c.*,
        p.line_of_business,
        p.coverage_limit,
        coalesce(pay.cleared_payment_amount, 0) as cleared_payment_amount,
        coalesce(pay.payment_count, 0) as payment_count,
        greatest(c.reported_paid_amount, coalesce(pay.cleared_payment_amount, 0)) as paid_amount,
        greatest(c.reserve_amount - c.reported_paid_amount, 0) as outstanding_reserve,
        date_diff('day', c.loss_date, cast(c.reported_at as date)) as reporting_delay_days
    from latest_claim c
    left join {{ ref('dim_policy_current') }} p using (policy_id)
    left join payments pay using (claim_id)
)

select
    *,
    paid_amount + outstanding_reserve as total_incurred,
    least(
        100,
        severity * 15
        + case when reporting_delay_days > 7 then 15 else 0 end
        + case when reserve_amount > coverage_limit * 0.5 then 10 else 0 end
        + case when source_system = 'partner_api' then 5 else 0 end
    ) as risk_score
from enriched

