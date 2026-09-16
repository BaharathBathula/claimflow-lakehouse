with source as (
    select *
    from read_parquet(
        '{{ env_var("CLAIMFLOW_BRONZE_PATH", "data/lake/bronze") }}/entity=policy/**/*.parquet',
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
    policy_id,
    customer_id,
    customer_name_token,
    customer_email_token,
    line_of_business,
    state,
    cast(effective_date as date) as effective_date,
    cast(expiration_date as date) as expiration_date,
    cast(annual_premium as decimal(18, 2)) as annual_premium,
    cast(coverage_limit as decimal(18, 2)) as coverage_limit,
    cast(deductible as decimal(18, 2)) as deductible,
    status
from deduplicated
where event_rank = 1

