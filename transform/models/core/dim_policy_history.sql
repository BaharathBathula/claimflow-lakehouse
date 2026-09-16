with versioned as (
    select
        *,
        lead(occurred_at) over (partition by policy_id order by occurred_at, event_id) as next_valid_from
    from {{ ref('stg_policies') }}
)

select
    md5(policy_id || '|' || cast(occurred_at as varchar)) as policy_version_key,
    policy_id,
    customer_id,
    customer_name_token,
    customer_email_token,
    line_of_business,
    state,
    effective_date,
    expiration_date,
    annual_premium,
    coverage_limit,
    deductible,
    status,
    occurred_at as valid_from,
    next_valid_from as valid_to,
    next_valid_from is null as is_current
from versioned

