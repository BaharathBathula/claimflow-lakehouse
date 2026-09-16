from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(os.getenv("CLAIMFLOW_DB_PATH", "data/warehouse/claimflow.duckdb"))

st.set_page_config(page_title="ClaimFlow Command Center", page_icon="⚡", layout="wide")
st.title("ClaimFlow · Claims Command Center")
st.caption("Real-time insurance operations metrics from the Gold lakehouse layer")

if not DB_PATH.exists():
    st.error("Warehouse not found. Run `make demo`, then refresh this page.")
    st.stop()


@st.cache_data(ttl=30)
def query(sql: str) -> pd.DataFrame:
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return connection.execute(sql).fetchdf()
    finally:
        connection.close()


kpis = query("select * from gold.claims_kpis").iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total claims", f"{int(kpis.total_claims):,}")
c2.metric("Open claims", f"{int(kpis.open_claims):,}")
c3.metric("Total incurred", f"${float(kpis.total_incurred):,.0f}")
c4.metric("High-risk queue", f"{int(kpis.high_risk_claims):,}")

metrics = query("select * from gold.daily_claim_metrics")
line_options = ["All", *sorted(metrics.line_of_business.dropna().unique().tolist())]
selected_line = st.selectbox("Line of business", line_options)
filtered = metrics if selected_line == "All" else metrics[metrics.line_of_business == selected_line]

left, right = st.columns(2)
daily = filtered.groupby("loss_date", as_index=False)[["claim_count", "total_incurred"]].sum()
left.plotly_chart(
    px.line(daily, x="loss_date", y="claim_count", title="Claim volume by loss date"),
    use_container_width=True,
)
by_line = metrics.groupby("line_of_business", as_index=False)["total_incurred"].sum()
right.plotly_chart(
    px.bar(
        by_line,
        x="line_of_business",
        y="total_incurred",
        title="Total incurred by line of business",
        labels={"total_incurred": "Total incurred ($)"},
    ),
    use_container_width=True,
)

st.subheader("Claims requiring attention")
high_risk = query("select * from gold.high_risk_claims limit 100")
st.dataframe(
    high_risk[
        [
            "claim_id",
            "line_of_business",
            "state",
            "status",
            "severity",
            "risk_score",
            "total_incurred",
            "adjuster_id",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)
st.caption(f"Data as of {kpis.data_as_of} · Synthetic data only")
