with source as (
    select *
    from read_parquet(
        '{{ env_var("CLAIMFLOW_BRONZE_PATH", "data/lake/bronze") }}/entity=claim/**/*.parquet',
        union_by_name = true
    )
),

deduplicated as (
    select *, row_number() over (partition by event_id order by ingested_at desc) as event_rank
    from source
)

select
    event_id,
    event_type,
    cast(occurred_at as timestamptz) as occurred_at,
    cast(ingested_at as timestamptz) as ingested_at,
    claim_id,
    policy_id,
    claimant_name_token,
    claimant_email_token,
    cast(loss_date as date) as loss_date,
    cast(reported_at as timestamptz) as reported_at,
    claim_type,
    state,
    cast(reserve_amount as decimal(18, 2)) as reserve_amount,
    cast(paid_amount as decimal(18, 2)) as reported_paid_amount,
    status,
    adjuster_id,
    cast(severity as integer) as severity,
    source_system
from deduplicated
where event_rank = 1

