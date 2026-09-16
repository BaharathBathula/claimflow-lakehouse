with source as (
    select *
    from read_parquet(
        '{{ env_var("CLAIMFLOW_BRONZE_PATH", "data/lake/bronze") }}/entity=payment/**/*.parquet',
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
    payment_id,
    claim_id,
    cast(payment_date as date) as payment_date,
    cast(amount as decimal(18, 2)) as amount,
    payment_type,
    payee_name_token,
    payment_status
from deduplicated
where event_rank = 1

